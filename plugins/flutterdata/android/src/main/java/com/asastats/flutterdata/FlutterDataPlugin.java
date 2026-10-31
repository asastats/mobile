package com.asastats.flutterdata;

import android.content.Context;
import android.util.Base64;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/** Reads what the old Flutter app saved under the same application id (docs/logbook.md). */
@CapacitorPlugin(name = "FlutterData")
public class FlutterDataPlugin extends Plugin {

    /** Flutter's preferences file and its "flutter."-prefixed key (mobileapp AppConstants.ADDRESS). */
    static final String FILE = "FlutterSharedPreferences";
    static final String ADDRESS_KEY = "flutter.address";

    @PluginMethod
    public void readAddresses(PluginCall call) {
        String raw;
        try {
            raw = getContext().getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(ADDRESS_KEY, null);
        } catch (ClassCastException error) {
            raw = null;
        }
        JSArray addresses = new JSArray();
        for (String entry : FlutterList.decode(raw, value -> Base64.decode(value, Base64.DEFAULT))) {
            addresses.put(entry);
        }
        JSObject result = new JSObject();
        result.put("addresses", addresses);
        call.resolve(result);
    }
}
