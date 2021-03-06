from django.db import models, connection

def generateDataCube(owner_name=None, subject=None, timing=None, start_date=None, end_date=None):
    assert timing in [False, 'year', 'week', 'month']
    
    dbquery = "SELECT {0}, {1}, {2}, count(*) FROM images {4} GROUP BY {3} {5};"

    zero = "owner_name" if owner_name else "null"
    one = "subject" if subject else "null"
    two = "date_trunc('%s', timing)"%(timing) if timing else "null"

    # GROUP BY clause
    three = ""
    if owner_name: three += "owner_name, "
    if subject:    three += "subject, "
    if timing:     three += "3, "
    if len(three) > 0: three = three[:-2]

    # WHERE clause
    four = ""
    if start_date or end_date:
        four += "WHERE "
    if start_date:
        four += "timing >= '%s' " % start_date
    elif end_date:
        four += "timing < ('%s'::date + '1 day'::interval) " % end_date
    if end_date and start_date:
        four += "AND timing < ('%s'::date + '1 day'::interval) " % end_date

    # ORDER BY clause
    five = "ORDER BY date_trunc('%s', timing)"%(timing) if timing else ''

    dbquery = dbquery.format(zero, one, two, three, four, five)
    if not any([owner_name, subject, timing]):
        dbquery = dbquery[:-11]
    
    cursor = connection.cursor()
    cursor.execute(dbquery)
    result = cursor.fetchall()
    
    json = list()

    for db_row in result:
        row = dict()
        if owner_name:
            if db_row[0] is None:
                row["Owner"] = "&lt;No Owner&gt;"
            else:
                row["Owner"] = db_row[0]
        if subject:
            if db_row[1] is None:
                row["Subject"] = "&lt;No Subject&gt;"
            else:
                row["Subject"] = db_row[1]
        if timing:
            # timing_col = {"year":"Year", "Month
            if db_row[2] is None:
                row["Timing"] = "&lt;No Date&gt;"
            elif timing == 'year':
                row["Timing"] = "%d" % (db_row[2].year)
            elif timing == 'month':
                row["Timing"] = "%d-%02d" % (db_row[2].year, db_row[2].month)
            elif timing == 'week':
                row["Timing"] = "%d-%02d-%02d" % (db_row[2].year, db_row[2].month, db_row[2].day)
        
        row["Count"] = db_row[3]
        json.append(row)

    print(dbquery)
    return json
