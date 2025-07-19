# django5-tutorial

<table>
  <tr>
    <td width="50%">Enable Multi-Factor Authentication</td>
    <td width="50%">Login examples</td>
  </tr>
  <tr>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/enableMFA.webp"></td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/loginView.webp"></td>
  </tr>
  <tr>
    <td width="50%">To activate multi-factor authentication (MFA), ensure your profile includes a current mobile number and email address. Verification codes will be sent to both, and must be validated before MFA can be enabled.</td>
    <td width="50%">
      <ul>
        <li>Logged-in users may revisit the login page to sign in as a different user; doing so will log out the current session.</li>
        <li>For accounts with MFA enabled, an OTP must be provided via authenticator app, email, or SMS.</li>
        <li>To prevent spamming, additional OTP requests are throttled with a 45-second cooldown.</li>
        <li>If required input fields from the MFA modal form are tampered with before submission (e.g. via HTML manipulation), a technical error will be displayed.</li>
      </ul>
    </td>
  </tr>
</table>
