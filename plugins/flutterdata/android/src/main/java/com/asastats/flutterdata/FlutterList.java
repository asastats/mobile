package com.asastats.flutterdata;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InvalidClassException;
import java.io.ObjectInputStream;
import java.io.ObjectStreamClass;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Function;

/**
 * Decodes a string list as Flutter's shared_preferences_android stored it: JSON since
 * plugin 2.3.0, a Java-serialized list before (docs/logbook.md). Anything else is empty.
 */
final class FlutterList {

    /** Base64 of "This is the prefix for a list."; the plugin's own constant. */
    static final String LIST_PREFIX = "VGhpcyBpcyB0aGUgcHJlZml4IGZvciBhIGxpc3Qu";
    static final String JSON_PREFIX = LIST_PREFIX + "!";

    private FlutterList() {}

    /**
     * @param raw the stored string, or null
     * @param base64 decoder for the legacy form (android.util.Base64 in the app)
     * @return the list's strings, or an empty list when raw is not a readable list
     */
    static List<String> decode(String raw, Function<String, byte[]> base64) {
        if (raw == null) return Collections.emptyList();
        if (raw.startsWith(JSON_PREFIX)) return parseJson(raw.substring(JSON_PREFIX.length()));
        if (raw.startsWith(LIST_PREFIX)) {
            try {
                return deserialize(base64.apply(raw.substring(LIST_PREFIX.length())));
            } catch (IllegalArgumentException error) {
                return Collections.emptyList();
            }
        }
        return Collections.emptyList();
    }

    /** A JSON array of strings; anything else, or any malformed text, is empty. */
    static List<String> parseJson(String json) {
        List<String> out = new ArrayList<>();
        int[] at = {skip(json, 0)};
        if (!expect(json, at, '[')) return Collections.emptyList();
        at[0] = skip(json, at[0]);
        if (expect(json, at, ']')) return trailing(json, at[0]) ? out : Collections.emptyList();
        while (true) {
            at[0] = skip(json, at[0]);
            String value = string(json, at);
            if (value == null) return Collections.emptyList();
            out.add(value);
            at[0] = skip(json, at[0]);
            if (expect(json, at, ',')) continue;
            if (expect(json, at, ']')) return trailing(json, at[0]) ? out : Collections.emptyList();
            return Collections.emptyList();
        }
    }

    private static boolean trailing(String json, int at) {
        return skip(json, at) == json.length();
    }

    private static int skip(String json, int at) {
        while (at < json.length() && " \t\r\n".indexOf(json.charAt(at)) >= 0) at++;
        return at;
    }

    private static boolean expect(String json, int[] at, char wanted) {
        if (at[0] < json.length() && json.charAt(at[0]) == wanted) {
            at[0]++;
            return true;
        }
        return false;
    }

    /** One JSON string at at[0], moving past it; null if there is none. */
    private static String string(String json, int[] at) {
        if (!expect(json, at, '"')) return null;
        StringBuilder out = new StringBuilder();
        while (at[0] < json.length()) {
            char c = json.charAt(at[0]++);
            if (c == '"') return out.toString();
            if (c != '\\') {
                out.append(c);
                continue;
            }
            if (at[0] >= json.length()) return null;
            char e = json.charAt(at[0]++);
            int simple = "\"\\/bfnrt".indexOf(e);
            if (simple >= 0) {
                out.append("\"\\/\b\f\n\r\t".charAt(simple));
            } else if (e == 'u' && at[0] + 4 <= json.length()) {
                try {
                    out.append((char) Integer.parseInt(json.substring(at[0], at[0] + 4), 16));
                } catch (NumberFormatException error) {
                    return null;
                }
                at[0] += 4;
            } else {
                return null;
            }
        }
        return null;
    }

    /** The legacy form: only an ArrayList of Strings is let through. */
    static List<String> deserialize(byte[] bytes) {
        try (ObjectInputStream in = new ListOnlyInputStream(bytes)) {
            Object value = in.readObject();
            if (!(value instanceof List)) return Collections.emptyList();
            List<String> out = new ArrayList<>();
            for (Object item : (List<?>) value) {
                if (item instanceof String) out.add((String) item);
            }
            return out;
        } catch (IOException | ClassNotFoundException error) {
            return Collections.emptyList();
        }
    }

    /** Refuses every class but ArrayList, so the stored bytes cannot build anything else. */
    private static final class ListOnlyInputStream extends ObjectInputStream {
        ListOnlyInputStream(byte[] bytes) throws IOException {
            super(new ByteArrayInputStream(bytes));
        }

        @Override
        protected Class<?> resolveClass(ObjectStreamClass desc) throws IOException, ClassNotFoundException {
            if (!ArrayList.class.getName().equals(desc.getName())) {
                throw new InvalidClassException(desc.getName(), "not allowed");
            }
            return super.resolveClass(desc);
        }
    }
}
