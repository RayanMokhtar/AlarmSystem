package com.example.homesecure;

public class AlertHistoryItem {

    private final String alertId;
    private final String dateTime;
    private final String message;

    public AlertHistoryItem(String alertId, String dateTime, String message) {
        this.alertId = alertId;
        this.dateTime = dateTime;
        this.message = message;
    }

    public String getAlertId() {
        return alertId;
    }

    public String getDateTime() {
        return dateTime;
    }

    public String getMessage() {
        return message;
    }
}
