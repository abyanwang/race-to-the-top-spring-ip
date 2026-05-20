# race-to-the-top-spring-ip

This project is ZHANG, Furui's(student Id:21270141) 2025-2026 Spring independent project advised by Professor Ke Yi.

This repository implements the R2T Algorithm based on this paper([https://www.cse.ust.hk/~yi**ke**/R2T.pdf](https://www.cse.ust.hk/~yike/R2T.pdf "https://www.cse.ust.hk/~yike/R2T.pdf")).

The database.py is using the sqlalchemy library to manage table creation and data loading.

The Q3.py and Q5.py are used to generate intermediated csv files.

The R2TAlgorithmMulti.py contains the R2T process and the LP-based truncation method. It evaluates R2T on Q5 to protect customer and supplier.

The R2TAlgorithmSingle.py inherit the R2TAlgorithmMulti.py and implement single primary private relation protection for Q3. It mainly protects customer.

The R2TMultiGsq.py is used to test the influence of different gsq on algorithm. The R2TSingleMultiGsq.py is similar to R2TMultiGsq.py.
