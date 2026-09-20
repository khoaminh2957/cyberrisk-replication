"""Replication of Florackis, Louca, Michaely & Weber, "Cybersecurity Risk", RFS 36 (2023) 351-407.

Module map (paper section -> module):
  2.2  crawl 10-K / Item 1A ............ edgar.py
  App. A keyword rules ................. keywords.py, extract.py
  2.3  training sample (PRC) ........... training.py
  2.4  word vectors + Eq. (1)(2) ....... roots.py, measure.py
  3.2  disclosure language (Table 2) ... language.py
  App. B variables ..................... variables.py
  3    validation (Tables 1-6) ......... validation.py
  4.1-4.2 portfolios (Tables 7-8) ...... portfolios.py
  4.3  Fama-MacBeth (Table 9) .......... fama_macbeth.py
  4.4  factor + Google SVI (Table 10) .. factor.py, gtrends.py
  5    SolarWinds (Tables 11-12) ....... solarwinds.py
  6    robustness (IA7-IA14) ........... robustness.py
"""
