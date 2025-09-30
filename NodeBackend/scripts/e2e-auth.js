const http = require('http');

function request(method, path, data) {
  const payload = data ? Buffer.from(JSON.stringify(data)) : null;
  const options = {
    hostname: 'localhost',
    port: 8000,
    path,
    method,
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': payload ? Buffer.byteLength(payload) : 0
    }
  };

  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => (body += chunk));
      res.on('end', () => {
        try {
          const json = JSON.parse(body || '{}');
          resolve({ status: res.statusCode, body: json });
        } catch (e) {
          resolve({ status: res.statusCode, body: { raw: body } });
        }
      });
    });
    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

(async () => {
  const mobile = '+911234567890';
  const email = 'test@example.com';
  const password = 'secret123';

  console.log('1) send-otp');
  const send = await request('POST', '/api/auth/send-otp', { mobile_number: mobile, email });
  console.log('->', send.status, send.body);
  if (send.status !== 200) process.exit(1);
  const otp = send.body.otp;

  console.log('2) verify-otp');
  const verify = await request('POST', '/api/auth/verify-otp', { mobile_number: mobile, otp_code: otp });
  console.log('->', verify.status, verify.body);
  if (verify.status !== 200) process.exit(1);

  console.log('3) signup');
  const signup = await request('POST', '/api/auth/signup', {
    fullname: 'Test User',
    email,
    mobile_number: mobile,
    password,
    confirm_password: password,
    otp_code: otp
  });
  console.log('->', signup.status, signup.body);
  if (signup.status !== 201 && signup.status !== 409) process.exit(1);

  console.log('4) login');
  const login = await request('POST', '/api/auth/login', { email, password });
  console.log('->', login.status, login.body);
  if (login.status !== 200) process.exit(1);

  console.log('✅ E2E auth flow completed');
})();
