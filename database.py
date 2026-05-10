import os
import io

import sys
# /Library/PostgreSQL/15/scripts/runpsql.sh; exit
#CREATE DATABASE tpch_scale_10 建一个database

import sqlalchemy
from sqlalchemy import (
    create_engine, Column, Integer, String, DECIMAL, Date, ForeignKey, Index, DOUBLE, PrimaryKeyConstraint, text
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import reflection

Base = declarative_base()
engine = None  
Session = None

database_name = 'tpch_scale_10'
dataset = ''
data_path = '/Users/free/Projects/ipdata1.0/'
relations = ["REGION", "NATION", "SUPPLIER", "CUSTOMER", "ORDERS", "LINEITEM"]


db_user = "postgres"
db_password = "peng!free"
db_host = "localhost"
db_port = "5432"

# define DDL
class Region(Base):
    __tablename__ = 'region'
    
    r_regionkey = Column(Integer, nullable=False, primary_key=True)
    r_name = Column(String(25), nullable=False)
    r_comment = Column(String(152))

    __table_args__ = (
        Index('r_i', 'r_regionkey'),
    )


class Nation(Base):
    __tablename__ = 'nation'
    n_nationkey = Column(Integer, nullable=False, primary_key=True)  # 原始主键
    n_name = Column(String(25), nullable=False)
    n_regionkey = Column(Integer, nullable=False)
    n_comment = Column(String(152))

    __table_args__ = (
        Index('n_i', 'n_nationkey'),
    )


class Supplier(Base):
    __tablename__ = 'supplier'
    s_suppkey = Column(Integer, nullable=False, primary_key=True)  # 原始主键
    s_name = Column(String(25), nullable=False)
    s_address = Column(String(40), nullable=False)
    s_nationkey = Column(Integer, nullable=False)
    s_phone = Column(String(15), nullable=False)
    s_acctbal = Column(DECIMAL(15, 2), nullable=False)
    s_comment = Column(String(101), nullable=False)

    __table_args__ = (
        Index('s_i', 's_suppkey'),
    )


class Customer(Base):
    __tablename__ = 'customer'
    c_custkey = Column(Integer, nullable=False, primary_key=True)  # 原始主键
    c_name = Column(String(25), nullable=False)
    c_address = Column(String(40), nullable=False)
    c_nationkey = Column(Integer, nullable=False)
    c_phone = Column(String(15), nullable=False)
    c_acctbal = Column(DECIMAL(15, 2), nullable=False)
    c_mktsegment = Column(String(10), nullable=False)
    c_comment = Column(String(117), nullable=False)

    
    __table_args__ = (
        Index('c_i', 'c_custkey'),
    )


class Orders(Base):
    __tablename__ = 'orders'

    o_orderkey = Column(Integer, nullable=False, primary_key=True)  # 原始主键
    o_custkey = Column(Integer, nullable=False)
    o_orderstatus = Column(String(1), nullable=False)
    o_totalprice = Column(DECIMAL(15, 2), nullable=False)
    o_orderdate = Column(Date, nullable=False)
    o_orderpriority = Column(String(15), nullable=False)
    o_clerk = Column(String(15), nullable=False)
    o_shippriority = Column(Integer, nullable=False)
    o_comment = Column(String(79), nullable=False)

    __table_args__ = (
        Index('o_i', 'o_orderkey'),
    )


class LineItem(Base):
    __tablename__ = 'lineitem'
    l_orderkey = Column(Integer, nullable=False)
    l_partkey = Column(Integer, nullable=False)
    l_suppkey = Column(Integer, nullable=False)
    l_linenumber = Column(Integer, nullable=False)
    l_quantity = Column(DECIMAL(15, 2), nullable=False)
    l_extendedprice = Column(DECIMAL(15, 2), nullable=False)
    l_discount = Column(DECIMAL(15, 2), nullable=False)
    l_tax = Column(DECIMAL(15, 2), nullable=False)
    l_returnflag = Column(String(1), nullable=False)
    l_linestatus = Column(String(1), nullable=False)
    l_shipdate = Column(Date, nullable=False)
    l_commitdate = Column(Date, nullable=False)
    l_receiptdate = Column(Date, nullable=False)
    l_shipinstruct = Column(String(25), nullable=False)
    l_shipmode = Column(String(10), nullable=False)
    l_comment = Column(String(44), nullable=False)

    __table_args__ = (
        # Index('l_i', 'l_partkey', 'l_suppkey'),
        
        PrimaryKeyConstraint('l_orderkey', 'l_linenumber'),
    )

def readData2Db():
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        for element in relations:
            table_name = element.lower()
            element_file_path = os.path.join(data_path, table_name + ".tbl")
            print(element_file_path)

            if not os.path.exists(element_file_path):
                print(f"Warning: File not found: {element_file_path}")
                continue

            processed_content = io.StringIO()
            #末尾有|，会报错需要清理
            with open(element_file_path, 'r', encoding='utf-8') as input_file:
                for line in input_file:
                    clean_line = line.rstrip('\r\n').removesuffix('|')
                    processed_content.write(clean_line + '\n')

            processed_content.seek(0)

            cur.copy_from(processed_content, table_name, sep='|')
            print(f"Successfully loaded {table_name}!")

        conn.commit()
        print("Data import completed successfully!")
    except Exception as e:
        print("Load Error" + e)
        conn.rollback()
    finally:
        conn.close()

def create_table():
    global engine, Session

    
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{database_name}"

    print(f"Connecting to database with URL: {db_url}")
    engine = create_engine(db_url, echo=False)
    #Base.metadata.drop_all(engine)  

    Base.metadata.create_all(engine)
    print("Database tables created successfully!")
    Session = sessionmaker(bind=engine)

def main():
    global database_name, dataset, db_user, db_password, db_host, db_port

    create_table()
    readData2Db()

if __name__ == "__main__":
    main()