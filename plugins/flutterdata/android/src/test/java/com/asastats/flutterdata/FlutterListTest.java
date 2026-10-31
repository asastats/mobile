package com.asastats.flutterdata;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.function.Function;
import org.junit.Test;

public class FlutterListTest {

    private static final String A = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU";
    private static final Function<String, byte[]> B64 = value -> Base64.getDecoder().decode(value);

    private static byte[] serialize(Object value) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
            out.writeObject(value);
        }
        return bytes.toByteArray();
    }

    private static String legacy(Object value) throws IOException {
        return FlutterList.LIST_PREFIX + Base64.getEncoder().encodeToString(serialize(value));
    }

    // decode

    @Test
    public void nullIsEmpty() {
        assertEquals(Collections.emptyList(), FlutterList.decode(null, B64));
    }

    @Test
    public void aPlainStringIsEmpty() {
        assertEquals(Collections.emptyList(), FlutterList.decode(A, B64));
    }

    @Test
    public void readsTheJsonForm() {
        String raw = FlutterList.JSON_PREFIX + "[\"" + A + "\",\"asastats.algo\"]";
        assertEquals(Arrays.asList(A, "asastats.algo"), FlutterList.decode(raw, B64));
    }

    @Test
    public void readsTheLegacyForm() throws IOException {
        ArrayList<String> list = new ArrayList<>(Arrays.asList("asastats.algo", A));
        assertEquals(list, FlutterList.decode(legacy(list), B64));
    }

    @Test
    public void badBase64IsEmpty() {
        assertEquals(Collections.emptyList(), FlutterList.decode(FlutterList.LIST_PREFIX + "%%%", B64));
    }

    // parseJson

    @Test
    public void emptyArrays() {
        assertEquals(Collections.emptyList(), FlutterList.parseJson("[]"));
        assertEquals(Collections.emptyList(), FlutterList.parseJson(" [ ] \n"));
    }

    @Test
    public void whitespaceBetweenItems() {
        assertEquals(Arrays.asList("a", "b"), FlutterList.parseJson("\t[ \"a\" ,\r\n \"b\" ]"));
    }

    @Test
    public void escapes() {
        assertEquals(
                Collections.singletonList("\"\\/\b\f\n\r\tAé"),
                FlutterList.parseJson("[\"\\\"\\\\\\/\\b\\f\\n\\r\\t\\u0041\\u00e9\"]"));
    }

    @Test
    public void malformedJsonIsEmpty() {
        String[] bad = {
            "", "{}", "[", "[\"a\"", "[\"a\",]", "[\"a\" \"b\"]", "[1]", "[\"a\"] x", "[] x",
            "[\"a", "[\"a\\", "[\"\\u1", "[\"\\x\"]", "[\"\\u12\"]", "[\"\\u12G4\"]",
        };
        for (String json : bad) {
            assertEquals(json, Collections.emptyList(), FlutterList.parseJson(json));
        }
    }

    // deserialize

    @Test
    public void legacyListKeepsOnlyStrings() throws IOException {
        // null and a nested list need no refused class, so they reach the String check.
        ArrayList<Object> list = new ArrayList<>(Arrays.asList("a.algo", null, new ArrayList<String>(), A));
        assertEquals(Arrays.asList("a.algo", A), FlutterList.deserialize(serialize(list)));
    }

    @Test
    public void legacyNonStringItemsAreRefusedWithTheirClass() throws IOException {
        // An Integer inside needs its class resolved, which the allow-list refuses.
        ArrayList<Object> list = new ArrayList<>(Arrays.asList("a.algo", 7));
        assertEquals(Collections.emptyList(), FlutterList.deserialize(serialize(list)));
    }

    @Test
    public void legacyOtherClassesAreRefused() throws IOException {
        assertEquals(Collections.emptyList(), FlutterList.deserialize(serialize(new HashMap<String, String>())));
        assertEquals(Collections.emptyList(), FlutterList.deserialize(serialize(new Marker())));
    }

    @Test
    public void legacyStringIsNotAList() throws IOException {
        assertEquals(Collections.emptyList(), FlutterList.deserialize(serialize(A)));
    }

    @Test
    public void legacyGarbageIsEmpty() {
        assertEquals(Collections.emptyList(), FlutterList.deserialize(new byte[] {1, 2, 3}));
        assertTrue(FlutterList.deserialize(new byte[0]).isEmpty());
    }

    private static final class Marker implements Serializable {
        private static final long serialVersionUID = 1L;
    }
}
