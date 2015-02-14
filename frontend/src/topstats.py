import psycopg2
import time
import tplE, datadb
from psycopg2._psycopg import adapt

__author__ = 'soroosh'


def getStatLoad(hostId, days='8'):
    days += 'days'
    sql = ""
    if not tplE._settings['run_aggregations']:
        sql = """
         SELECT
                  xaxis, stat_load_15min
                FROM (
                      SELECT
                        xaxis,
                        (sum(d_self_time) OVER (ORDER BY xaxis ASC ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) / (1*15*60*1000))::numeric(6,2) AS stat_load_15min
                      FROM
                        ( SELECT
                            date_trunc('hour'::text, t.ssd_timestamp) + floor(date_part('minute'::text, t.ssd_timestamp) / 15::double precision) * '00:15:00'::interval AS xaxis,
                            sum(t.total_time) AS d_self_time
                          FROM ( SELECT
                                   ssd.ssd_timestamp,
                                   ssd.ssd_total_time AS total_time
                                 FROM
                                   monitor_data.stat_statements_data ssd
                                 WHERE
                                   ssd.ssd_host_id = """ + str(adapt(hostId)) + """
                                   AND ssd.ssd_timestamp > now() - """ + str(adapt(days)) + """::interval
                                 WINDOW w AS
                                   ( PARTITION BY ssd.ssd_query_id ORDER BY ssd.ssd_timestamp )
                               ) t
                          GROUP BY
                            date_trunc('hour'::text, t.ssd_timestamp) + floor(date_part('minute'::text, t.ssd_timestamp) / 15::double precision) * '00:15:00'::interval
                          ORDER BY
                            date_trunc('hour'::text, t.ssd_timestamp) + floor(date_part('minute'::text, t.ssd_timestamp) / 15::double precision) * '00:15:00'::interval
                        ) loadTable
                    ) a
                    ORDER BY
                      xaxis
        """

    conn = datadb.getDataConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(sql)

    load = {'stat_load_15min': []}

    lastTime = None
    skip15min = 0

    for record in cur:
        currentTime = int(time.mktime(record['xaxis'].timetuple()) * 1000)
        if lastTime != None:
            if currentTime - lastTime > (15 * 60 * 1000):
                skip15min = 2

        if skip15min > 0:
            skip15min -= 1
        else:
            load['stat_load_15min'].append((record['xaxis'], round(record['stat_load_15min'], 2) ))

        lastTime = int(time.mktime(record['xaxis'].timetuple()) * 1000)

    cur.close()
    conn.close()

    return load
