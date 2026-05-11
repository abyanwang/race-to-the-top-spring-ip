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
        SELECT c_custkey, SUM(l_extendedprice * (1 - l_discount)) as value
        FROM customer, orders, lineitem
        WHERE c_mktsegment = 'BUILDING'
          AND o_custkey = c_custkey
          AND l_orderkey = o_orderkey
          AND o.o_orderdate  < '1995-03-13'
          AND l.l_shipdate   > '1995-03-13'
        GROUP BY c_custkey;
        """

        # SELECT c_custkey, count(1) as value
        # FROM customer, orders, lineitem
        # WHERE
        #    o_custkey = c_custkey
        #   AND l_orderkey = o_orderkey
        #   and o_orderdate<date'1997-01-01' 
        #     and l_shipdate>date'1994-01-01'
        # GROUP BY c_custkey;

         

        result = session.execute(text(sql))
        rows = result.all()

        output_file = "query/sum_query_output_q3.csv"
        total_count = 0
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['custom_id', 'cnt'])
            for row in rows:
                writer.writerow(row)
                total_count += row.value
        print(total_count)

    except Exception as e:
        print(f"Exception: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()