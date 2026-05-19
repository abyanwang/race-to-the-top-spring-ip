import os
import io
import sys

import sqlalchemy
from sqlalchemy import (
    create_engine, Column, Integer, String, DECIMAL, Date, ForeignKey, Index, DOUBLE, PrimaryKeyConstraint, text
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import reflection
from dotenv import load_dotenv

Base = declarative_base()

config = {
    "0.125":{
        "database_name":'tpch_scale_0125',
        "data_path":"/Users/free/Projects/ipdata0.125"
    },
    "0.25":{
        "database_name":'tpch_scale_025',
        "data_path":"/Users/free/Projects/ipdata0.25"
    },
    "0.5":{
        "database_name":'tpch_scale_050',
        "data_path":"/Users/free/Projects/ipdata0.5"
    },
    "1.0":{
        "database_name":'tpch_scale_10',
        "data_path":"/Users/free/Projects/ipdata1.0"
    }
}

relations = ["REGION", "NATION", "SUPPLIER", "CUSTOMER", "ORDERS", "LINEITEM"]

load_dotenv()
db_user = "postgres"
db_password = os.getenv("db_password")
db_host = "localhost"
db_port = "5432"


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
    n_nationkey = Column(Integer, nullable=False, primary_key=True)  
    n_name = Column(String(25), nullable=False)
    n_regionkey = Column(Integer, nullable=False)
    n_comment = Column(String(152))

    __table_args__ = (
        Index('n_i', 'n_nationkey'),
    )


class Supplier(Base):
    __tablename__ = 'supplier'
    s_suppkey = Column(Integer, nullable=False, primary_key=True)  
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
    c_custkey = Column(Integer, nullable=False, primary_key=True)  
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

    o_orderkey = Column(Integer, nullable=False, primary_key=True)  
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
        PrimaryKeyConstraint('l_orderkey', 'l_linenumber'),
    )



def create_table(db_name):
    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    engine = create_engine(db_url, echo=False)

    Base.metadata.drop_all(engine)
    
    Base.metadata.create_all(engine)
    
    return engine

def readData2Db(engine, current_data_path):
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        for element in relations:
            table_name = element.lower()
            element_file_path = os.path.join(current_data_path, table_name + ".tbl")
            print(f"Processing: {element_file_path}")

            processed_content = io.StringIO()
            
            #remove 无用的|
            with open(element_file_path, 'r', encoding='utf-8') as input_file:
                for line in input_file:
                    clean_line = line.rstrip('\r\n').removesuffix('|')
                    processed_content.write(clean_line + '\n')

            processed_content.seek(0)

            cur.copy_from(processed_content, table_name, sep='|')
            print(f"Successfully loaded {table_name}!")

        conn.commit()
    except Exception as e:
        print(f"Failed to load {table_name}: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    for scale, settings in config.items():
        db_name = settings["database_name"]
        current_data_path = settings["data_path"]
                
        engine = create_table(db_name)
        
        readData2Db(engine, current_data_path)
        
        engine.dispose()
        

if __name__ == "__main__":
    main()