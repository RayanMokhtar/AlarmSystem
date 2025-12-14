package com.example.homesecure;

import java.util.ArrayList;
import java.util.List;

public final class AlertHistoryRepository {

    private AlertHistoryRepository() {
    }

    public static List<AlertHistoryItem> getFakeHistory() {
        List<AlertHistoryItem> items = new ArrayList<>();
        items.add(new AlertHistoryItem("AL-1042", "14/12/2025 21:12", AlertHistoryItem.Classification.CONFIRMED_ALERT));
        items.add(new AlertHistoryItem("AL-1041", "14/12/2025 20:58", AlertHistoryItem.Classification.FALSE_ALARM));
        items.add(new AlertHistoryItem("AL-1040", "14/12/2025 19:33", AlertHistoryItem.Classification.CONFIRMED_ALERT));
        items.add(new AlertHistoryItem("AL-1039", "13/12/2025 23:09", AlertHistoryItem.Classification.FALSE_ALARM));
        items.add(new AlertHistoryItem("AL-1038", "13/12/2025 18:47", AlertHistoryItem.Classification.FALSE_ALARM));
        items.add(new AlertHistoryItem("AL-1037", "12/12/2025 07:14", AlertHistoryItem.Classification.CONFIRMED_ALERT));
        items.add(new AlertHistoryItem("AL-1036", "11/12/2025 16:05", AlertHistoryItem.Classification.FALSE_ALARM));
        return items;
    }
}
