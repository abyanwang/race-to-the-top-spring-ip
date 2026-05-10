import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import db_user, db_password, db_host, db_port, database_name
import csv


def main():
    try:
        db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{database_name}"
        engine = create_engine(db_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        sql = """
        SELECT 
    s.s_suppkey AS s_suppkey,
    c.c_custkey AS c_custkey,
    COUNT(*) AS cnt
FROM supplier s
JOIN lineitem l ON s.s_suppkey = l.l_suppkey
JOIN orders o ON l.l_orderkey = o.o_orderkey
JOIN customer c ON o.o_custkey = c.c_custkey
JOIN nation n ON c.c_nationkey = n.n_nationkey
JOIN region r ON n.n_regionkey = r.r_regionkey
WHERE s.s_nationkey = n.n_nationkey
GROUP BY 
    s.s_suppkey, 
    c.c_custkey;
        """

        result = session.execute(text(sql))
        rows = result.all()

        output_file = "query/count_query_output_q5.csv"
        total_count = 0
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['s_suppkey', 'c_custkey', 'cnt'])
            for row in rows:
                writer.writerow(row)
                total_count += row.cnt
        print(total_count)

    except Exception as e:
        print(f"Exception: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()