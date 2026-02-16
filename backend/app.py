from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pytz
from db_config import get_db_connection

app = Flask(__name__)
CORS(app)

IST = pytz.timezone("Asia/Kolkata")

@app.route("/")
def home():
    return "Issue Tracker Backend Running"

@app.route("/issues", methods=["GET"])
def get_issues():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

  
    search = request.args.get("search")
    status = request.args.get("status")
    category = request.args.get("category")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    query = "SELECT * FROM issues WHERE 1=1"
    values = []

   
    if search and search.strip():
        search = search.strip()
        if search.isdigit():
            query += " AND id = %s"
            values.append(int(search))
        else:
            query += " AND subject LIKE %s"
            values.append(f"%{search}%")

    
    if status and status.strip():
        query += " AND status = %s"
        values.append(status)

   
    if category and category.strip():
        query += " AND category = %s"
        values.append(category)

   
    if from_date and from_date.strip():
        query += " AND created_date >= %s"
        values.append(from_date.strip() + " 00:00:00")

  
    if to_date and to_date.strip():
        query += " AND created_date <= %s"
        values.append(to_date.strip() + " 23:59:59")

    query += " ORDER BY created_date DESC"

    cursor.execute(query, values)
    data = cursor.fetchall()

    
    for issue in data:
        issue["created_date"] = (
            issue["created_date"].strftime("%Y-%m-%d %H:%M:%S")
            if issue["created_date"] else None
        )
        issue["last_update"] = (
            issue["last_update"].strftime("%Y-%m-%d %H:%M:%S")
            if issue["last_update"] else None
        )

    cursor.close()
    conn.close()

    return jsonify(data)



@app.route("/create-issue", methods=["POST"])
def create_issue():
    data = request.get_json(force=True)
    print("✅ FINAL DATA:", data)

    now = datetime.now(IST)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO issues
            (subject, category, status, severity, reporter, assignee, description, created_date, last_update)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data.get("subject"),
            data.get("category"),
            data.get("status"),
            data.get("severity"),
            data.get("reporter"),
            data.get("assignee"),
            data.get("description"),
            now,
            now
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Issue created successfully"}), 201

    except Exception as e:
        print("❌ INSERT ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/update-issue/<int:issue_id>", methods=["PUT"])
def update_issue(issue_id):
    data = request.get_json(force=True)
    print("🔁 UPDATE DATA:", data)

    status = data.get("status")
    close_reason = data.get("close_reason")


    if status == "Reopened":
        close_reason = None

    severity = data.get("severity")
    assignee = data.get("assignee")
    description = data.get("description") or ""
    close_reason = data.get("close_reason") if status == "Closed" else None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE issues
            SET status=%s,
                category=%s,
                severity=%s,
                assignee=%s,
                description=%s,
                close_reason=%s,
                last_update=%s
            WHERE id=%s
        """, (
            status,
             data.get("category"),
            severity,
            assignee,
            description,
            close_reason,
            datetime.now(IST),
            issue_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Issue updated successfully"})

    except Exception as e:
        print("❌ UPDATE ERROR:", e)
        return jsonify({"error": str(e)}), 500





@app.route("/delete-issue/<int:issue_id>", methods=["DELETE"])
def delete_issue(issue_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM issues WHERE id = %s", (issue_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Issue deleted"})


@app.route("/reports", methods=["GET"])
def get_reports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    reports = {}

    
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM issues
        GROUP BY status
    """)
    reports["status"] = cursor.fetchall()

 
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM issues
        GROUP BY category
    """)
    reports["category"] = cursor.fetchall()

    
    cursor.execute("""
        SELECT severity, COUNT(*) as count
        FROM issues
        GROUP BY severity
    """)
    reports["severity"] = cursor.fetchall()

  
    cursor.execute("""
        SELECT assignee, COUNT(*) as count
        FROM issues
        GROUP BY assignee
    """)
    reports["assignee"] = cursor.fetchall()

    
    cursor.execute("""
        SELECT close_reason, COUNT(*) as count
        FROM issues
        WHERE status = 'Closed'
        AND close_reason IS NOT NULL
        GROUP BY close_reason
    """)
    reports["close_reason"] = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(reports)




if __name__ == "__main__":
    app.run(debug=True)
