package com.example.homesecure;

import android.os.Bundle;
import android.view.View;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

public class AlertHistoryActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_alert_history);

        View btnBack = findViewById(R.id.btnBack);
        btnBack.setOnClickListener(v -> finish());

        RecyclerView recyclerView = findViewById(R.id.rvAlertHistoryFull);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        recyclerView.setAdapter(new AlertHistoryAdapter(AlertHistoryRepository.getFakeHistory()));
    }
}
