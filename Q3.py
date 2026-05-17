import os
import csv
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database import config, db_user, db_password, db_host, db_port

def execute_and_export(scale, db_name):
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # sql = """
        # SELECT c_custkey, count(1) as value
        # FROM customer, orders, lineitem
        # WHERE c_mktsegment = 'BUILDING'
        #   AND o_custkey = c_custkey
        #   AND l_orderkey = o_orderkey
        #   AND o_orderdate < '1995-03-15'
        #   AND l_shipdate > '1995-03-15'
        # GROUP BY c_custkey;
        # """
        
        
        # sql = """SELECT c_custkey, count(1) as value
        # FROM customer, orders, lineitem
        # WHERE o_custkey = c_custkey
        #   AND l_orderkey = o_orderkey
        #   AND o_orderdate < '1995-03-15'
        #   AND l_shipdate > '1995-03-15'
        # GROUP BY c_custkey;
        # """

        

        sql = """SELECT  c_custkey
                ,COUNT(1) AS value
            FROM customer, orders, lineitem
            WHERE c_custkey = o_custkey
            AND l_orderkey = o_orderkey
            AND o_orderdate < '1995-03-15'
            AND l_shipdate > '1995-03-15'
            GROUP BY  c_custkey
        """

        # sql = """SELECT  c_custkey
        #         ,sum(l_extendedprice*(1-l_discount)) AS value
        #     FROM customer, orders, lineitem
        #     WHERE c_custkey = o_custkey
        #     AND l_orderkey = o_orderkey
        #     AND o_orderdate < '1995-03-15'
        #     AND l_shipdate > '1995-03-15'
        #     GROUP BY  c_custkey
        # """

        print(f"Querying database: {db_name} (Scale: {scale})")
        result = session.execute(text(sql))
        rows = result.all()

        output_file = f"query/count_query_output_q3_scale_{scale}.csv"
        
        total_count = 0
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['custom_id', 'cnt'])
            for row in rows:
                writer.writerow(row)
                total_count += row.value
                
        print(f"Successfully exported {len(rows)} rows to {output_file}")
        print(f"Total sum (value): {total_count}")

    except Exception as e:
        print(f"Exception: {e}")
    finally:
        session.close()
        engine.dispose()

def main():
    for scale, settings in config.items():
        db_name = settings["database_name"]
        execute_and_export(scale, db_name)
        
if __name__ == "__main__":
    main()