import os
import csv
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


from database import config, db_user, db_host, db_port,db_password

# load_dotenv()

# db_password = os.getenv("db_password")
# print(db_password)

def execute_and_export(scale, db_name):
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        sql = """
        SELECT
            s_suppkey,
            c_custkey,
            count(1) AS value
        FROM
            customer,
            orders,
            lineitem,
            supplier,
            nation,
            region
        WHERE
            c_custkey = o_custkey
            AND l_orderkey = o_orderkey
            AND l_suppkey = s_suppkey
            AND c_nationkey = s_nationkey
            AND s_nationkey = n_nationkey
            AND n_regionkey = r_regionkey
            AND o_orderdate >= date '1994-01-01'
            AND o_orderdate < date '1994-01-01' + interval '1' year
        GROUP BY
            s_suppkey,
            c_custkey
        """

        # sql = """
        # SELECT
        #     s_suppkey,
        #     c_custkey,
        #     sum(l_extendedprice*(1-l_discount)) AS value
        # FROM
        #     customer,
        #     orders,
        #     lineitem,
        #     supplier,
        #     nation,
        #     region
        # WHERE
        #     c_custkey = o_custkey
        #     AND l_orderkey = o_orderkey
        #     AND l_suppkey = s_suppkey
        #     AND c_nationkey = s_nationkey
        #     AND s_nationkey = n_nationkey
        #     AND n_regionkey = r_regionkey
        #     AND o_orderdate >= date '1994-01-01'
        #     AND o_orderdate < date '1994-01-01' + interval '1' year
        # GROUP BY
        #     s_suppkey,
        #     c_custkey
        # """

        print(f"Querying database: {db_name} (Scale: {scale})...")
        result = session.execute(text(sql))
        rows = result.all()
        
        output_file = f"query/count_query_output_q5_scale_{scale}.csv"
        
        total_count = 0
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['s_suppkey', 'c_custkey', 'cnt'])
            
            for row in rows:
                writer.writerow(row)
                total_count += row.value
                
        print(f"exported {len(rows)} rows to {output_file}")
        print(f" sum (value): {total_count}\n")

    except Exception as e:
        print(f"Exception: {e}")
        raise
    finally:
        session.close()
        engine.dispose() 

def main():
    # 遍历 config 提取每个 scale 及其对应的数据库名
    for scale, settings in config.items():
        db_name = settings["database_name"]
        execute_and_export(scale, db_name)
        

if __name__ == "__main__":
    main()