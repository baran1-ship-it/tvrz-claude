package cz.baran.kancelar;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ContentResolver;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Hostitelská aktivita: celé uživatelské rozhraní běží ve WebView (assets/www),
 * tato třída zajišťuje přístup k souborům přes Storage Access Framework.
 */
public class MainActivity extends Activity {

    private static final int REQ_OPEN = 1;
    private static final int REQ_SAVE_AS = 2;

    private static final String[] OPEN_MIME = {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "application/vnd.oasis.opendocument.spreadsheet",
            "text/csv",
            "text/comma-separated-values",
            "application/octet-stream"
    };

    private WebView web;
    private boolean pageReady = false;

    /** Soubor připravený k převzetí z JavaScriptu (JSON). */
    private String pendingFile = null;
    /** Data čekající na zápis po výběru cíle „Uložit jako“. */
    private byte[] pendingSaveBytes = null;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setTextZoom(100);

        web.addJavascriptInterface(new Bridge(), "Android");
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                pageReady = true;
                if (pendingFile != null) notifyFileReady();
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, android.webkit.WebResourceRequest req) {
                // Odkazy z dokumentů otevírat v prohlížeči, ne v aplikaci.
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, req.getUrl()));
                } catch (Exception ignored) { }
                return true;
            }
        });
        web.loadUrl("file:///android_asset/www/index.html");

        handleIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }

    private void handleIntent(Intent intent) {
        if (intent == null) return;
        String action = intent.getAction();
        if ((Intent.ACTION_VIEW.equals(action) || Intent.ACTION_EDIT.equals(action)) && intent.getData() != null) {
            loadUri(intent.getData(), false);
        }
    }

    @Override
    public void onBackPressed() {
        if (!pageReady) { super.onBackPressed(); return; }
        web.evaluateJavascript("window.App ? App.onBack() : false", value -> {
            if (!"true".equals(value)) finish();
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_OPEN) {
            if (resultCode == RESULT_OK && data != null && data.getData() != null) {
                Uri uri = data.getData();
                takePermission(uri, data.getFlags());
                loadUri(uri, true);
            }
        } else if (requestCode == REQ_SAVE_AS) {
            byte[] bytes = pendingSaveBytes;
            pendingSaveBytes = null;
            if (resultCode == RESULT_OK && data != null && data.getData() != null && bytes != null) {
                Uri uri = data.getData();
                takePermission(uri, data.getFlags());
                boolean ok = writeBytes(uri, bytes);
                String name = displayName(uri);
                callJs("App.onSavedAs(" + ok + "," + JSONObject.quote(uri.toString()) + "," + JSONObject.quote(name) + ")");
            } else {
                callJs("App.onSavedAs(false,null,null)");
            }
        }
    }

    private void takePermission(Uri uri, int flags) {
        try {
            int f = flags & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            getContentResolver().takePersistableUriPermission(uri, f);
        } catch (Exception ignored) {
            // Některé zdroje (např. příloha e-mailu) trvalé oprávnění nepodporují.
        }
    }

    private void loadUri(Uri uri, boolean persistent) {
        new Thread(() -> {
            try {
                byte[] bytes = readBytes(uri);
                JSONObject o = new JSONObject();
                o.put("name", displayName(uri));
                o.put("uri", uri.toString());
                o.put("persistent", persistent || hasPersistedPermission(uri));
                o.put("data", Base64.encodeToString(bytes, Base64.NO_WRAP));
                pendingFile = o.toString();
                runOnUiThread(() -> { if (pageReady) notifyFileReady(); });
            } catch (Exception e) {
                runOnUiThread(() -> toast("Soubor nelze otevřít: " + e.getMessage()));
                callJs("App.onOpenFailed(" + JSONObject.quote(uri.toString()) + ")");
            }
        }).start();
    }

    private boolean hasPersistedPermission(Uri uri) {
        for (android.content.UriPermission p : getContentResolver().getPersistedUriPermissions()) {
            if (p.getUri().equals(uri)) return true;
        }
        return false;
    }

    private void notifyFileReady() {
        callJs("App.onFileReady()");
    }

    private void callJs(String js) {
        runOnUiThread(() -> web.evaluateJavascript(js, null));
    }

    private byte[] readBytes(Uri uri) throws Exception {
        ContentResolver cr = getContentResolver();
        try (InputStream in = cr.openInputStream(uri)) {
            if (in == null) throw new Exception("prázdný zdroj");
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[64 * 1024];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            return out.toByteArray();
        }
    }

    private boolean writeBytes(Uri uri, byte[] bytes) {
        ContentResolver cr = getContentResolver();
        for (String mode : new String[]{"wt", "w"}) {
            try (OutputStream out = cr.openOutputStream(uri, mode)) {
                if (out == null) continue;
                out.write(bytes);
                out.flush();
                return true;
            } catch (Exception ignored) { }
        }
        return false;
    }

    private String displayName(Uri uri) {
        String name = null;
        try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (c != null && c.moveToFirst()) name = c.getString(0);
        } catch (Exception ignored) { }
        if (name == null) {
            name = uri.getLastPathSegment();
            if (name != null && name.contains("/")) name = name.substring(name.lastIndexOf('/') + 1);
        }
        return name == null ? "soubor" : name;
    }

    private void toast(String msg) {
        Toast.makeText(this, msg, Toast.LENGTH_LONG).show();
    }

    /** Rozhraní volané z JavaScriptu (objekt window.Android). */
    private class Bridge {

        @JavascriptInterface
        public void pickFile() {
            runOnUiThread(() -> {
                Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("*/*");
                i.putExtra(Intent.EXTRA_MIME_TYPES, OPEN_MIME);
                i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                        | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                        | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                try {
                    startActivityForResult(i, REQ_OPEN);
                } catch (Exception e) {
                    toast("Nelze otevřít výběr souborů");
                }
            });
        }

        @JavascriptInterface
        public void openUri(String uri) {
            loadUri(Uri.parse(uri), true);
        }

        @JavascriptInterface
        public String takeFile() {
            String f = pendingFile;
            pendingFile = null;
            return f;
        }

        /** Přepíše původní soubor. Vrací true při úspěchu. */
        @JavascriptInterface
        public boolean save(String uri, String base64) {
            try {
                byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
                return writeBytes(Uri.parse(uri), bytes);
            } catch (Exception e) {
                return false;
            }
        }

        /** Nechá uživatele vybrat umístění a název; výsledek přijde do App.onSavedAs. */
        @JavascriptInterface
        public void saveAs(String suggestedName, String mime, String base64) {
            pendingSaveBytes = Base64.decode(base64, Base64.DEFAULT);
            runOnUiThread(() -> {
                Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType(mime);
                i.putExtra(Intent.EXTRA_TITLE, suggestedName);
                try {
                    startActivityForResult(i, REQ_SAVE_AS);
                } catch (Exception e) {
                    pendingSaveBytes = null;
                    toast("Nelze otevřít dialog pro uložení");
                }
            });
        }

        @JavascriptInterface
        public void toast(String msg) {
            runOnUiThread(() -> MainActivity.this.toast(msg));
        }

        /** Systémový tisk – umožňuje i „Uložit jako PDF“. */
        @JavascriptInterface
        public void print(String jobName) {
            runOnUiThread(() -> {
                android.print.PrintManager pm = (android.print.PrintManager) getSystemService(PRINT_SERVICE);
                String name = jobName == null || jobName.isEmpty() ? "Dokument" : jobName;
                pm.print(name, web.createPrintDocumentAdapter(name), new android.print.PrintAttributes.Builder().build());
            });
        }

        @JavascriptInterface
        public void exitApp() {
            runOnUiThread(MainActivity.this::finish);
        }
    }
}
