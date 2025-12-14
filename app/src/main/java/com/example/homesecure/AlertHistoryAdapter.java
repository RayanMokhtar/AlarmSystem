package com.example.homesecure;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;

import java.util.List;

public class AlertHistoryAdapter extends RecyclerView.Adapter<AlertHistoryAdapter.ViewHolder> {

    private final List<AlertHistoryItem> items;

    public AlertHistoryAdapter(List<AlertHistoryItem> items) {
        this.items = items;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_alert_history_row, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        AlertHistoryItem item = items.get(position);

        holder.tvAlertId.setText(item.getAlertId());
        holder.tvAlertDateTime.setText(item.getDateTime());
        holder.tvAlertClassification.setText(item.getClassificationLabel());

        Context context = holder.itemView.getContext();
        int colorRes = (item.getClassification() == AlertHistoryItem.Classification.CONFIRMED_ALERT)
                ? R.color.green_success
                : R.color.red_danger;
        holder.tvAlertClassification.setTextColor(ContextCompat.getColor(context, colorRes));
    }

    @Override
    public int getItemCount() {
        return items == null ? 0 : items.size();
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        final TextView tvAlertId;
        final TextView tvAlertDateTime;
        final TextView tvAlertClassification;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvAlertId = itemView.findViewById(R.id.tvAlertId);
            tvAlertDateTime = itemView.findViewById(R.id.tvAlertDateTime);
            tvAlertClassification = itemView.findViewById(R.id.tvAlertClassification);
        }
    }
}
