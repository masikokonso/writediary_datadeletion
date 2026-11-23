
import os
import re
import time
import uuid

import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Firebase configuration
# Configure these as environment variables on your hosting platform.
FB_HOST = os.environ.get(
    "FB_HOST",
    "https://aviabustout-default-rtdb.firebaseio.com"
).rstrip("/")

FB_AUTH = os.environ.get("FB_AUTH", "")

# WriteDiary configuration
REQUESTS_PATH = "writediary_deletion_requests"

APP_NAME = "WriteDiary"

SUPPORT_EMAIL = os.environ.get(
    "SUPPORT_EMAIL",
    "support@ngelicyber.com"
)


def identifier_is_valid(identifier: str) -> bool:
    identifier = identifier.strip()

    email_pattern = re.compile(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    phone_pattern = re.compile(
        r"^(?:\+254|0)[17]\d{8}$"
    )

    return bool(
        email_pattern.fullmatch(identifier)
        or phone_pattern.fullmatch(identifier)
    )


def normalize_phone(identifier: str) -> str:
    identifier = identifier.strip()

    if identifier.startswith("0") and len(identifier) == 10:
        return "+254" + identifier[1:]

    return identifier


PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">

<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<meta name="description"
content="Request deletion of your WriteDiary account and personal diary data.">

<title>Delete My Account & Data — {{ app_name }}</title>

<style>

:root {
    --ink: #16241d;
    --ink-soft: #4b5c53;
    --paper: #f6f4ee;
    --card: #ffffff;
    --line: #dcd6c8;
    --accent: #1f7a4d;
    --accent-dark: #14512f;
    --danger: #a8371f;
    --danger-bg: #fbf0ec;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: "Iowan Old Style",
                 "Palatino Linotype",
                 Georgia, serif;
    line-height: 1.5;
}

.wrap {
    max-width: 620px;
    margin: 0 auto;
    padding: 56px 24px 80px;
}

header.top {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 40px;
    border-bottom: 1px solid var(--line);
    padding-bottom: 18px;
}

.mark {
    font-weight: 700;
    font-size: 19px;
    letter-spacing: 0.01em;
}

.mark span {
    color: var(--accent);
}

header.top .tag {
    font-family: -apple-system,
                 BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
    font-size: 12px;
    color: var(--ink-soft);
    text-align: right;
}

h1 {
    font-size: 30px;
    line-height: 1.2;
    margin: 0 0 10px;
    max-width: 22ch;
}

p.lede {
    font-family: -apple-system,
                 BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
    color: var(--ink-soft);
    font-size: 15px;
    max-width: 46ch;
    margin: 0 0 36px;
}

section.block {
    margin-bottom: 34px;
}

h2 {
    font-family: -apple-system,
                 BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: var(--ink);
    margin: 0 0 12px;
}

ul.data-list {
    font-family: -apple-system,
                 BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
    font-size: 14.5px;
    color: var(--ink-soft);
    margin: 0;
    padding-left: 0;
    list-style: none;
}

ul.data-list li {
    padding: 10px 0;
    border-top: 1px solid var(--line);
    display: flex;
    justify-content: space-between;
    gap: 16px;
}

ul.data-list li:last-child {
    border-bottom: 1px solid var(--line);
}

ul.data-list li .what {
    color: var(--ink);
}

ul.data-list li .retain {
    color: var(--ink-soft);
    font-size: 13px;
    white-space: nowrap;
}

form.card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 4px;
    padding: 28px;
    font-family: -apple-system,
                 BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
}

label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 6px;
}

input[type=text] {
    width: 100%;
    padding: 12px 14px;
    border: 1px solid var(--line);
    border-radius: 3px;
    font-size: 15px;
    font-family: inherit;
    margin-bottom: 18px;
    background: #fcfbf8;
}

input[type=text]:focus {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
}

.confirm-row {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    margin-bottom: 22px;
    font-size: 13.5px;
    color: var(--ink-soft);
}

.confirm-row input {
    margin-top: 3px;
}

button.submit {
    width: 100%;
    padding: 14px 18px;
    background: var(--danger);
    color: #fff;
    border: none;
    border-radius: 3px;
    font-size: 15px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
}

button.submit:hover {
    background: #8a2c18;
}

button.submit:disabled {
    background: #c9a89f;
    cursor: not-allowed;
}

#msg {
    margin-top: 16px;
    font-size: 14px;
    padding: 12px 14px;
    border-radius: 3px;
    display: none;
}

#msg.ok {
    display: block;
    background: #eaf4ee;
    color: var(--accent-dark);
    border: 1px solid #bfe0cc;
}

#msg.err {
    display: block;
    background: var(--danger-bg);
    color: var(--danger);
    border: 1px solid #eecbc0;
}

.note {
    font-family: -apple-system,
                 BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
    color: var(--ink-soft);
    font-size: 13px;
    margin-top: 15px;
}

footer {
    margin-top: 48px;
    font-family: -apple-system,
                 BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
    font-size: 12.5px;
    color: var(--ink-soft);
}

footer a {
    color: var(--accent-dark);
}

@media (max-width: 480px) {
    .wrap {
        padding: 35px 18px 60px;
    }

    h1 {
        font-size: 27px;
    }

    form.card {
        padding: 22px;
    }

    ul.data-list li {
        font-size: 13px;
    }

    ul.data-list li .retain {
        font-size: 12px;
    }
}

</style>
</head>

<body>

<div class="wrap">

<header class="top">
    <div class="mark">
        <span>{{ app_name }}</span>
    </div>

    <div class="tag">
        Account &amp; Data Deletion
    </div>
</header>

<h1>Delete your account and personal data</h1>

<p class="lede">
    Your privacy matters to us. If you no longer
    wish to use {{ app_name }}, you can request
    permanent deletion of your account and
    associated personal diary information.

    Submit your request using the email address
    or phone number registered with your account.

    We aim to process verified deletion requests
    within 30 days.
</p>

<section class="block">

<h2>WHAT GETS DELETED</h2>

<ul class="data-list">

<li>
    <span class="what">
        Account profile and personal information
    </span>
    <span class="retain">Deleted</span>
</li>

<li>
    <span class="what">
        Personal diary and journal entries
    </span>
    <span class="retain">Deleted</span>
</li>

<li>
    <span class="what">
        Saved notes and written memories
    </span>
    <span class="retain">Deleted</span>
</li>

<li>
    <span class="what">
        Attached photos and media, if stored
    </span>
    <span class="retain">Deleted</span>
</li>

<li>
    <span class="what">
        Diary preferences and account settings
    </span>
    <span class="retain">Deleted</span>
</li>

</ul>

<p class="note">
    Data stored only on your device may need
    to be deleted directly within the app or
    by clearing its local storage. Some
    information may be retained where legally
    required.
</p>

</section>

<form class="card" id="delForm">

<label for="identifier">
    Email address used on
    {{ app_name }}
</label>

<input
    type="text"
    id="identifier"
    name="identifier"
    placeholder="you@example.com or 0712345678"
    autocomplete="username"
    required
>

<div class="confirm-row">

<input type="checkbox" id="confirm" required>

<label for="confirm"
       style="font-weight:400; margin:0;">
    I understand that deleting my
    {{ app_name }} account and its associated
    data is permanent and cannot be undone.
</label>

</div>

<button
    type="submit"
    class="submit"
    id="submitBtn">
    Request account deletion
</button>

<div id="msg" role="status" aria-live="polite"></div>

</form>

<footer>

<p>
    Need help with account deletion?
    Contact
    <a href="mailto:{{ support_email }}">
        {{ support_email }}
    </a>.
</p>

<p>
    WriteDiary respects your privacy and
    is committed to protecting your
    personal journal information.
</p>

<p>
    &copy; {{ year }} WriteDiary.
    All rights reserved.
</p>

</footer>

</div>

<script>

const form = document.getElementById('delForm');
const msg = document.getElementById('msg');
const btn = document.getElementById('submitBtn');

form.addEventListener('submit', async (e) => {

    e.preventDefault();

    const identifier = document
        .getElementById('identifier')
        .value.trim();

    msg.className = '';
    msg.style.display = 'none';

    btn.disabled = true;
    btn.textContent = 'Submitting…';

    try {

        const res = await fetch('/api/delete-request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                identifier: identifier
            })
        });

        const data = await res.json();

        if (res.ok) {

            msg.textContent = data.message;
            msg.className = 'ok';

            form.reset();

            btn.textContent = 'Request submitted';

        } else {

            msg.textContent =
                data.error ||
                'Something went wrong. Please try again.';

            msg.className = 'err';

            btn.disabled = false;

            btn.textContent =
                'Request account deletion';
        }

    } catch (err) {

        msg.textContent =
            'Network error. Please try again.';

        msg.className = 'err';

        btn.disabled = false;

        btn.textContent =
            'Request account deletion';
    }

});

</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(
        PAGE_TEMPLATE,
        app_name=APP_NAME,
        support_email=SUPPORT_EMAIL,
        year=time.gmtime().tm_year
    )


@app.route("/api/delete-request", methods=["POST"])
def delete_request():

    data = request.get_json(silent=True) or {}

    identifier = (
        data.get("identifier") or ""
    ).strip()

    if not identifier or not identifier_is_valid(identifier):
        return jsonify({
            "error": (
                "Enter a valid email address "
                "or Kenyan phone number."
            )
        }), 400

    if not FB_AUTH:
        return jsonify({
            "error": (
                "Server not configured. "
                "Please contact support."
            )
        }), 500

    identifier_norm = normalize_phone(identifier)

    request_id = str(uuid.uuid4())

    payload = {
        "app": APP_NAME,
        "identifier": identifier_norm,
        "status": "pending",
        "requestedAt": int(time.time() * 1000),
        "source": "web-deletion-form"
    }

    try:

        resp = requests.put(
            f"{FB_HOST}/{REQUESTS_PATH}/{request_id}.json",
            params={
                "auth": FB_AUTH
            },
            json=payload,
            timeout=10
        )

        resp.raise_for_status()

    except requests.RequestException:

        return jsonify({
            "error": (
                "Could not submit your request "
                "right now. Please try again shortly."
            )
        }), 502

    return jsonify({
        "message": (
            "Your WriteDiary account deletion "
            "request has been received. "
            "Following account verification, "
            "we aim to delete your account "
            "and associated data within 30 days."
        )
    }), 200


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
