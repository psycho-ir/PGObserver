import psycopg2
import time
from time_utils import makeTimeIntervalReadable
import tplE, datadb
from psycopg2._psycopg import adapt

__author__ = 'soroosh'
import tplE

AVG_RUNTIME_ORDER = "sum(ssd_total_time) / sum(ssd_calls) desc"
TOTAL_RUNTIME_ORDER = "sum(ssd_total_time) desc"
TOTAL_CALLS_ORDER = "sum(ssd_calls) desc"


def getSQL(interval=None, hostId=1):
    selected_users = tplE._settings["filter_top_stats_for_users"]
    user_filter_query = ""
    if interval:
        interval = "AND ssd_timestamp > " + interval
    else:
        interval = ""

    if selected_users and len(selected_users) > 0:
        user_filter_query = "AND ssd_user_id IN (%s)" % (reduce(lambda x, y: str(x) + ',' + str(y), selected_users))

    sql = """select ssd_query,sum(ssd_calls) ssd_calls,sum(ssd_total_time) ssd_total_time,sum(ssd_blks_read) ssd_blks_read,sum(ssd_blks_written) ssd_blks_written,sum(ssd_temp_blks_read) ssd_temp_blks_read,sum(ssd_temp_blks_written) ssd_temp_blks_written
              from stat_statements_data
              where
              ssd_host_id = %s
              %s
              %s
              group by ssd_query"""

    return sql % (hostId, user_filter_query, interval)


def getTop10Interval(order=AVG_RUNTIME_ORDER, interval=None, hostId=1, limit=10):
    sql = getSQL(interval, hostId) + " order by " + order + " limit " + str(limit)

    conn = datadb.getDataConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute(sql)

    stats = []

    for record in cur:
        record['ssd_total_time'] = makeTimeIntervalReadable(record['ssd_total_time'])
        record['ssd_blks_read'] = makeTimeIntervalReadable(record['ssd_blks_read'])
        record['ssd_blks_written'] = makeTimeIntervalReadable(record['ssd_blks_written'])
        record['ssd_temp_blks_read'] = makeTimeIntervalReadable(record['ssd_temp_blks_read'])
        record['ssd_temp_blks_written'] = makeTimeIntervalReadable(record['ssd_temp_blks_written'])
        stats.append(record)

    conn.close()

    return stats


def getTop10AllTimes(order, hostId=1):
    return getTop10Interval(order)


def getTop10LastXHours(order, hours=1, hostId=1, limit=10):
    return getTop10Interval(order, "('now'::timestamp - %s::interval)" % ( adapt("%s hours" % ( hours, )), ), hostId, limit)


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
