package com.asastats.app;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.SystemClock;
import androidx.annotation.NonNull;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;
import com.google.firebase.messaging.RemoteMessage;
import io.capawesome.capacitorjs.plugins.firebase.messaging.MessagingService;
import java.util.Map;

/** Shows an alert that arrives while the app is open; FCM draws only background ones (docs/logbook.md). */
public class AlertMessagingService extends MessagingService {

    /** Also FCM's default_notification_channel_id in AndroidManifest.xml. */
    static final String CHANNEL_ID = "alerts";

    @Override
    public void onMessageReceived(@NonNull RemoteMessage remoteMessage) {
        super.onMessageReceived(remoteMessage);
        RemoteMessage.Notification notification = remoteMessage.getNotification();
        if (notification == null || !NotificationManagerCompat.from(this).areNotificationsEnabled()) {
            return;
        }
        createChannel(this);

        // The extras FCM puts on a background tap, so the plugin reports it as notificationActionPerformed.
        Intent tap = new Intent(this, MainActivity.class);
        for (Map.Entry<String, String> entry : remoteMessage.getData().entrySet()) {
            tap.putExtra(entry.getKey(), entry.getValue());
        }
        tap.putExtra("google.message_id", String.valueOf(remoteMessage.getMessageId()));
        int requestCode = (int) SystemClock.uptimeMillis();
        PendingIntent contentIntent = PendingIntent.getActivity(
            this,
            requestCode,
            tap,
            PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
        );

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_stat_asastats)
            .setColor(ContextCompat.getColor(this, R.color.notification_accent))
            .setContentTitle(notification.getTitle())
            .setContentText(notification.getBody())
            .setStyle(new NotificationCompat.BigTextStyle().bigText(notification.getBody()))
            .setContentIntent(contentIntent)
            .setAutoCancel(true);

        // Same tag replaces the earlier alert, as FCM does with android.notification.tag.
        String tag = notification.getTag() != null ? notification.getTag() : "FCM-Notification:" + requestCode;
        try {
            NotificationManagerCompat.from(this).notify(tag, 0, builder.build());
        } catch (SecurityException ignored) {
            // POST_NOTIFICATIONS revoked between the check and the post.
        }
    }

    /** The channel FCM uses for background alerts too; created before either needs it. */
    static void createChannel(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return;
        }
        NotificationManager manager = context.getSystemService(NotificationManager.class);
        if (manager.getNotificationChannel(CHANNEL_ID) == null) {
            manager.createNotificationChannel(
                new NotificationChannel(
                    CHANNEL_ID,
                    context.getString(R.string.notification_channel_alerts),
                    NotificationManager.IMPORTANCE_DEFAULT
                )
            );
        }
    }
}
