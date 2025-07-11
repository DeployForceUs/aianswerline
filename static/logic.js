let savedEmail = '';

function sendOtp() {
  const email = document.getElementById("email").value.toLowerCase();
  fetch("/send_otp_email", {
    method: "POST",
    body: new URLSearchParams({ email })
  })
  .then(res => res.json())
  .then(data => {
    if (data.message) {
      savedEmail = email;
      document.getElementById("otp-status").innerText = "✅ Code sent. Check your email!";
      document.getElementById("otp-form").classList.remove("hidden");
    } else {
      document.getElementById("otp-status").innerText = "❌ " + data.detail;
    }
  });
}

function verifyOtp() {
  const code = document.getElementById("otp-code").value;
  fetch("/verify_otp", {
    method: "POST",
    body: new URLSearchParams({ email: savedEmail, code })
  })
  .then(res => res.json())
  .then(data => {
    if (data.message === "Verified") {
      document.getElementById("verify-status").innerText = "✅ Verified!";
      if (data.linked) {
        showDashboard(savedEmail, data.phone, data.tokens || 0);
      } else {
        document.getElementById("phone-form").classList.remove("hidden");
      }
    } else {
      document.getElementById("verify-status").innerText = "❌ " + data.detail;
    }
  });
}

function bindPhone() {
  let phone = document.getElementById("phone").value.trim();
  if (!phone.startsWith("+1")) {
    phone = "+1" + phone;
  }

  fetch("/bind_phone", {
    method: "POST",
    body: new URLSearchParams({ email: savedEmail, phone })
  })
  .then(res => res.json())
  .then(data => {
    if (data.message === "Verified") {
      document.getElementById("bind-status").innerText = "✅ Phone linked!";
      showDashboard(data.email, data.phone, data.tokens || 0);
    } else {
      document.getElementById("bind-status").innerText = "❌ " + data.detail;
    }
  });
}

function showDashboard(email, phone, tokens) {
  document.getElementById("phone-form").classList.add("hidden");
  document.getElementById("otp-form").classList.add("hidden");

  document.getElementById("dashboard-email").innerText = email;
  document.getElementById("dashboard-phone").innerText = phone;
  document.getElementById("dashboard-tokens").innerText = tokens;
  document.getElementById("dashboard").classList.remove("hidden");
}

function buyTokens(amount) {
  const phone = document.getElementById("dashboard-phone").innerText.trim();
  const url = `/create_order_payment?amount=${amount}&phone=${encodeURIComponent(phone)}`;
  window.location.href = url;
}
