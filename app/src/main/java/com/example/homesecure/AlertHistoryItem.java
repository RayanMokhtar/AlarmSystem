package com.example.homesecure;

public class AlertHistoryItem {

    public enum Classification {
        CONFIRMED_ALERT,
        FALSE_ALARM
    }

    private final String alertId;
    private final String dateTime;
    private final Classification classification;

    public AlertHistoryItem(String alertId, String dateTime, Classification classification) {
        this.alertId = alertId;
        this.dateTime = dateTime;
        this.classification = classification;
    }

    public String getAlertId() {
        return alertId;
    }

    public String getDateTime() {
        return dateTime;
    }

    public Classification getClassification() {
        return classification;
    }

    public String getClassificationLabel() {
        if (classification == Classification.CONFIRMED_ALERT) {
            return "Alerte confirmée";
        }
        return "Fausse alerte";
    }
}
