package de.zalando.pgobserver.gatherer;

import java.sql.Timestamp;


class StatStatementsValue {
    Timestamp timestamp;
    String query;
    long query_id;
    long calls;
    long total_time;
    long blks_read;
    long blks_written;
    long temp_blks_read;
    long temp_blks_written;
    int userId;

    @Override
    public String toString() {
        return "StatStatementsValue{" +
                "userId='" + userId + '\'' +
                "query='" + query + '\'' +
                "calls=" + calls +
                '}';
    }
}
