# How to use the app

<table>
  <tr>
    <td width="50%"><strong>Login Examples</strong></td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <br>
      Logged-in users may revisit the login page to sign in as a different user; doing so will log out the current session.
      <hr>
      For accounts with MFA enabled, an OTP must be provided via authenticator app, email, or SMS.
      <hr>
      To prevent spamming, additional OTP requests are throttled with a 45-second cooldown.
      <hr>
      If required input fields from the MFA modal form are tampered with before submission (e.g. via HTML manipulation), a technical error will be displayed.
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/loginView.webp"></td>
  </tr>
</table>

<table>
  <tr>
    <td width="50%"><strong>Add new model</strong></td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <br>
      To register a new model, the user must be logged in and click the “Add Model” link on the main page. They will be redirected to a form to create the model. Upon successful submission, they are returned to the main page and can delete their models at any time from there.
      <hr>
      <p>Users can search for models using the search input. Search results may include their own models as well as those created by other users. Available filters include:</p>
      <ul>
        <li>No creator</li>
        <li>Creator username</li>
        <li>Creator ID</li>
        <li>Country code</li>
      </ul>
      Depending on the selected filter, an additional input field may appear. For example, selecting “Creator ID” prompts the user to provide the corresponding ID.
      <hr>
      Models are loaded in batches of five per request via infinite scroll. Relevant models matching the search criteria are displayed first. As users scroll further, additional—possibly irrelevant—models will appear beneath the initial results.
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/models.webp"></td>
  </tr>
</table>

<table>
  <tr>
    <td width="50%"><strong>Enable Multi-Factor Authentication</strong></td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <br>
      To activate multi-factor authentication (MFA), ensure your profile includes a current mobile number and email address.
      <hr>
      Verification codes will be sent to both, and must be validated before MFA can be enabled.
      <hr>
      Users can disable MFA at any time from their profile page. Since this is a critical security setting, they will be prompted to confirm their password as a safeguard.
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/enableMFA.webp"></td>
  </tr>
</table>

<table>
  <tr>
    <td rowspan="2" valign="top">
      <br>
      Users can remove their account at any time from the profile page. Because this is a critical action, password confirmation is required to proceed.
      <hr>
      <p>Upon successful verification, a feedback panel appears displaying:</p>
      <ul>
        <li>A countdown indicating when the account is scheduled for deletion</li>
        <li>Optional technical reassessment details, accessible via a dropdown</li>
        <li>Key instructions outlining what users should know before and after the deletion is finalized</li>
        <li>Links to the site's privacy policy and terms & conditions for reference</li>
      </ul>
      <hr>
      Users may cancel the deletion schedule at any point before the countdown completes—no password verification required. Canceling the schedule resets the countdown; if reinitiated, a fresh 30-day deletion interval begins.
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/deleteUserSetting.webp"></td>
  </tr>
  <tr>
     <td>
      Account deletions are handled by a background scheduler running on a separate server. Eligible accounts are processed every 15 minutes. A secondary fallback scheduler ensures full deletion in case of interruptions or failure in the primary task.
      <hr>
      ⚠️ Once an account is deleted, it cannot be recovered—including any third-party integrations such as the associated Stripe customer account used for payments.
      <br>
    </td>
  </tr>
</table>
