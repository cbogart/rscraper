import sqlite3

        
def getConnection(dbname):
    # Open the database
    conn = sqlite3.connect(dbname)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma short_column_names=OFF;");
    conn.execute("pragma full_column_names=ON;");
    return conn

    
