# Purpose

The goal of this project is to support learning of the Django framework, with a primary focus on backend development. Along the way, it incorporates a variety of external services to meet different functional requirements. While the app is fundamentally backend-driven, certain advanced features—such as multi-factor authentication (MFA), donation payments, and user account deletion—introduce significant frontend complexity. As such, a solid understanding of JavaScript is recommended before exploring these sections: [JavaScript Intermediate Docs](https://1drv.ms/b/c/a8ea73639e1a076a/ETnwCT76VaxLvtN9ZxOtkNQB5X5aoPzHePCMs88QNS6Z9Q?e=XNWNiJ)

## Disclaimer

I am still a learner myself. Throughout development, I encountered and had to adopt many unfamiliar methodologies, which may have introduced occasional mistakes or inconsistencies in the documentation. Nevertheless, the process has been incredibly educational, and I hope others will find value in the experience and insights shared.

## Documentation & Project

To get started, simply **download** [Django.pdf](https://github.com/gubrus50/django5-tutorial/blob/main/Django.pdf) and follow the instructions inside.
Or open the via OneDrive: [Django Tutorial 2025.pdf](https://1drv.ms/b/c/a8ea73639e1a076a/EVDUEirS1zFAn9J2860DhY4BxuC9dLE2WM9R3mUjICeIQA?e=pwObhe)

<strong>NOTE</strong>:
<ul>
  <li>I recommend opening the file in two-page view on a separate monitor for easier navigation.</li>
  <br>
  <li>This project was mainly developed and tested in a Linux-based environment: RedHat family - Fedora.</li>
  <br>
  <li>This project is built using the latest stable release of Django and up-to-date pip packages as of July 2025. All dependencies have been actively maintained to ensure compatibility, security, and modern development practices.</li>
  <br>
  <li>
    This project makes extensive use of Bootstrap 5 components, which—while widely supported—may no longer be the preferred choice for building modern, scalable applications, especially given the recent shift in popularity toward Tailwind CSS. 
    <br><br>Nonetheless, I discovered several useful packages that simplified development and complemented Bootstrap's design system. They also helped streamline the documentation by saving visual and layout space, making the learning process more approachable.
  </li>
</ul>

<br>

# Key Features

1. [Login User](#login-user)<br>
2. [Register User](#register-user)<br>
3. [Models](#models)<br>
4. [Multi-Factor Authentication](#multi-factor-authentication)<br>
5. [Remove User](#remove-user)<br>
6. [Chat Rooms](#chat-rooms)<br>
7. [Payments](#payments)<br>
8. [Errors](#errors)<br>
9. [Contacting Support](#contacting-support)<br>
10. (...a work in progress, monitor tasks with flower + celery)

<br>

## Login User
<table>
  <tr>
    <td rowspan="2" valign="top">
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
  <tr>
    <td valign="top">
      ⚠️ A user's contact details—such as their phone number and email address—are masked using asterisk symbols <code>*</code> during MFA logging to provide minimal feedback and protect personal data.
      <br>
    </td>
  </tr>
</table>

<br>

## Register User
<table>
  <tr>
    <td width="50%" valign="top">
      <br>
      Visiting clients can register new users and optionally set a profile image during registration. Once registered, users are authenticated automatically and redirected to the main page. From their profile page, they can update their photo, password, and other account details at any time. If no image is provided, a default template image is automatically assigned.
      <hr>
      To handle media storage efficiently, the application integrates with Amazon S3 buckets. This setup ensures profile pictures are stored securely and reliably, leveraging AWS's globally distributed, scalable infrastructure. Offloading image management to S3 also simplifies server logic and improves performance across deployments.
      <hr>
      Users can delete their account anytime from the profile page, giving them full control over their data and online presence.
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/registerUserView.png"></td>
  </tr>
</table>

<br>

## Models
<table>
  <tr>
    <td rowspan="2" valign="top">
      <br>
      To register a new model, the user must be logged in and click the <code>Add Model</code> link on the main page. They will be redirected to a form to create the model. Upon successful submission, they are returned to the main page and can delete their models at any time from there.
      <hr>
      <p>Users can search for models using the search input. Search results may include their own models as well as those created by other users. Available filters include:</p>
      <ul>
        <li>No creator</li>
        <li>Creator username</li>
        <li>Creator ID</li>
        <li>Country code</li>
      </ul>
      <hr>
      Depending on the selected filter, an additional input field may appear. For example, selecting “Creator ID” prompts the user to provide the corresponding ID.
      <hr>
      Model creation is gated behind a reCAPTCHA challenge to prevent spam and abusive requests. This safeguard helps protect the integrity and performance of the application's services.
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/models.webp"></td>
  </tr>
  <tr>
    <td>
      Models are loaded in batches of five per request via infinite scroll. Relevant models matching the search criteria are displayed first. As users scroll further, additional—possibly irrelevant—models will appear beneath the initial results.
      <br>
    </td>
  </tr>
</table>

<br>

## Multi-Factor Authentication
<table>
  <tr>
    <td rowspan="2" valign="top">
      <br>
      To activate multi-factor authentication (MFA), ensure your profile includes a current mobile number and email address.
      <hr>
      Verification codes will be sent to both, and must be validated before MFA can be enabled.
      <hr>
      Users can disable MFA at any time from their profile page. Since this is a critical security setting, they will be prompted to confirm their password as a safeguard.
      <hr>
      ⚠️ MFA is currently enforced via <code>CustomLoginView()</code> only. Django’s default admin login bypasses this mechanism. To maintain consistent authentication security, consider routing admin login through the custom view—or disabling access to the admin panel "login" site entirely.
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/enableMFA.webp"></td>
  </tr>
  <tr>
    <td>
      ⚠️ This application utilizes Zoho and Twilio services to send One-Time Password (OTP) codes.
      <br>
    </td>
  </tr>
</table>

<br>

## Remove User
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
    <td valign="top">
      <br>
      Account deletions are handled by a background scheduler running on a separate server. Eligible accounts are processed every 15 minutes. A secondary fallback scheduler ensures full deletion in case of interruptions or failure in the primary task.
      <hr>
      ⚠️ Once an account is deleted, it cannot be recovered—including any third-party integrations such as the associated Stripe customer account used for payments.
      <br>
    </td>
  </tr>
</table>

<br>

## Chat Rooms
<table>
  <tr>
    <td rowspan="2" valign="top">
      <br>
      The platform supports real-time conversations using ASGI and WebSockets.
      <hr>
      <p>To start a direct chat, users can visit another user's profile and click the <code>Direct Message</code> button located below their profile picture.</p>
      <ul>
        <li>If a chatroom already exists between the two users, the logged-in user is redirected there.</li>
        <li>If not, a new direct chatroom is created automatically.</li>
      </ul>
      <hr>
      Users can revisit their active conversations anytime via the <code>My Chats</code> dropdown on their own profile page.
      <hr>
      <p>A public chatroom also exists, but it’s not currently linked on any page. To access it manually, navigate to: <code>localhost:8000/chat/</code></p>
      <p>The same goes for accessing other users, just use: <code>localhost:8000/users/profile/USER_ID</code></p>
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/chatRooms.webp"></td>
  </tr>
  <tr>
    <td>
      ⚠️ Conversations are not end-to-end encrypted. Messages can be viewed via the admin panel and should not be considered private. 🗑️ Chat histories associated with deleted users are automatically removed from the system.
      <br>
    </td>
  </tr>
</table>

<br>

## Payments
<table>
  <tr>
    <td rowspan="2" valign="top">
      <br>
      <p>There are two payment flows available via Stripe: <strong>Buy Plan</strong> and <strong>Donate</strong>. Both are accessible only to authenticated users:</p>
      <ul>
        <li><strong>Buy Plan:</strong> <code>localhost:8000/buy-plan</code></li>
        <li><strong>Donate:</strong> <code>localhost:8000/donate</code></li>
      </ul>
      <hr>
      <h4>Buy Plan</h4>
      <p>Users select from predefined plans via a dropdown. Backend validation enforces the selection, ensuring secure, tamper-proof payments.</p>
      <hr>
      <h4>Donate</h4>
      <p>This page allows users to enter a custom donation amount. Key features include:</p>
      <ul>
        <li>Polish-language support for all labels and error messages</li>
        <li>Localized country selector with flags for enhanced UX</li>
        <li>Address input with country-aware postcode validation</li>
        <li>Postcode patterns and available countries configurable via JSON</li>
        <li>Country exclusions enforced (e.g. Russia, North Korea)</li>
      </ul>
      <p>Although the example image shows a full address line, this feature is disabled in the current live implementation. Developers can manually re-enable it as needed.</p>
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/payments.webp"></td>
  </tr>
  <tr>
    <td valign="top">
      <br>
      ✅ Upon payment completion, users are greeted with a confirmation screen and may redirect themselves back to the homepage.
      <hr>
      ⚠️ Each user is tied to a Stripe customer ID. If absent, a new account is auto-generated when accessing the page—even if a prior account was unlinked.
      <br>
    </td>
  </tr>
</table>

<br>

## Errors
<table>
  <tr>
    <td rowspan="2" valign="top">
      <br>
      <ul>
        <li>
          <strong>400 Bad Request</strong><br>
          The server couldn’t understand the request due to malformed syntax. 
          <em>Example:</em> Submitting a form with missing or invalid fields, or a malformed JSON payload.
        </li>
        <br>
        <li>
          <strong>403 Forbidden</strong><br>
          The server understood the request but refuses to authorize it. 
          <em>Example:</em> Accessing a restricted admin page without proper credentials.
        </li>
        <br>
        <li>
          <strong>404 Not Found</strong><br>
          The requested resource couldn’t be found.<br>
          <em>Example:</em> A mistyped URL, or visiting a deleted page.
        </li>
        <br>
        <li>
          <strong>500 Internal Server Error</strong><br>
          A generic error indicating something went wrong on the server side. 
          <em>Example:</em> Unhandled exception, misconfigured middleware, or a broken database query.
        </li>
      </ul>
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/animated/errors.webp"></td>
  </tr>
  <tr>
    <td>
      <br>
      ⚠️ These error pages are shown only when <code>DEBUG = False</code> in your <code>settings.py</code>. When <code>DEBUG = True</code>, Django displays detailed debug pages instead, which are useful during development for diagnosing issues.
      <br>
    </td>
  </tr>
</table>

<br>

## Contacting Support
<table>
  <tr>
    <td rowspan="2" valign="top">
      <br>
      All users — whether logged in or not — can reach the support team via the direct URL: <code>http://localhost:8000/contact</code>.
      <hr>
      <p>To streamline communication, the form includes:</p>
      <ul>
        <li>📝 A pre-formatted message template</li>
        <li>🗂️ A selection of subject options to help route inquiries efficiently</li>
        <li>📧 A required client email field so our support team can follow up with a response</li>
      </ul>
      <hr>
      The contact form is protected by reCAPTCHA to block spam and automated abuse. Submissions are sent via a bot email connected to Zoho Mail, and repeated spam can trigger account suspension. That’s why keeping this protection in place is essential.
      <br>
    </td>
    <td width="50%"><img src="https://github.com/gubrus50/django5-tutorial/blob/main/screenshots/contactFormView.png"></td>
  </tr>
  <tr>
    <td valign="top">
      ⚠️ The page is not currently linked in the UI and must be accessed manually.
      <br>
    </td>
  </tr>
</table>
