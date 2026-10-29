package com.asastats.nativesignin;

import android.content.pm.PackageManager;
import android.os.CancellationSignal;
import androidx.core.content.ContextCompat;
import androidx.credentials.Credential;
import androidx.credentials.CredentialManager;
import androidx.credentials.CredentialManagerCallback;
import androidx.credentials.CustomCredential;
import androidx.credentials.GetCredentialRequest;
import androidx.credentials.GetCredentialResponse;
import androidx.credentials.exceptions.GetCredentialException;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption;
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential;

/**
 * {@code NativeSignIn.isAvailable({provider})} → {@code {available}};
 * {@code NativeSignIn.signIn({provider, nonce, serverClientId})} →
 * {@code {idToken, givenName?, familyName?}}, rejecting with a
 * {@link NativeSignInRequest} message. Design: capacitor/O3-NATIVE-SIGNIN-DESIGN.md.
 */
@CapacitorPlugin(name = "NativeSignIn")
public class NativeSignInPlugin extends Plugin {

    private boolean busy;

    @PluginMethod
    public void isAvailable(PluginCall call) {
        JSObject result = new JSObject();
        result.put("available", NativeSignInRequest.supports(call.getString("provider")) && hasPlayServices());
        call.resolve(result);
    }

    @PluginMethod
    public void signIn(PluginCall call) {
        NativeSignInRequest request = NativeSignInRequest.create(
            call.getString("provider"), call.getString("nonce"), call.getString("serverClientId"));
        if (request == null) {
            call.reject(NativeSignInRequest.INVALID);
            return;
        }
        if (busy) {
            call.reject(NativeSignInRequest.BUSY);
            return;
        }
        busy = true;

        GetSignInWithGoogleOption option = new GetSignInWithGoogleOption.Builder(request.serverClientId)
            .setNonce(request.nonce)
            .build();
        GetCredentialRequest credentialRequest = new GetCredentialRequest.Builder()
            .addCredentialOption(option)
            .build();
        CredentialManager.create(getContext()).getCredentialAsync(
            getActivity(),
            credentialRequest,
            new CancellationSignal(),
            ContextCompat.getMainExecutor(getContext()),
            new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
                @Override
                public void onResult(GetCredentialResponse response) {
                    busy = false;
                    resolveCredential(call, response.getCredential());
                }

                @Override
                public void onError(GetCredentialException error) {
                    busy = false;
                    call.reject(NativeSignInRequest.failureFor(error.getType()));
                }
            }
        );
    }

    private void resolveCredential(PluginCall call, Credential credential) {
        if (!(credential instanceof CustomCredential)
            || !GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(credential.getType())) {
            call.reject(NativeSignInRequest.FAILED);
            return;
        }
        GoogleIdTokenCredential google;
        try {
            google = GoogleIdTokenCredential.createFrom(credential.getData());
        } catch (Exception e) {
            call.reject(NativeSignInRequest.FAILED);
            return;
        }
        JSObject result = new JSObject();
        result.put("idToken", google.getIdToken());
        result.put("givenName", google.getGivenName());
        result.put("familyName", google.getFamilyName());
        call.resolve(result);
    }

    private boolean hasPlayServices() {
        try {
            getContext().getPackageManager().getPackageInfo("com.google.android.gms", 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }
}
