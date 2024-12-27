/**
 * Variables
 */
const signupButton = document.getElementById('signup-button'),
    loginButton = document.getElementById('login-button'),
    userForms = document.getElementById('user_options-forms')

/**
 * Add event listener to the "Sign Up" button
 */
signupButton.addEventListener('click', () => {
  userForms.classList.remove('bounceRight')
  userForms.classList.add('bounceLeft')
}, false)

/**
 * Add event listener to the "Login" button
 */
loginButton.addEventListener('click', () => {
  userForms.classList.remove('bounceLeft')
  userForms.classList.add('bounceRight')
}, false)

/**
 * Handle Sign Up form submission
 */
const signupForm = document.querySelector('.user_forms-signup form');

signupForm.addEventListener('submit', async (e) => {
  e.preventDefault(); // Prevent default form submission

  // Collect form data
  const name = signupForm.querySelector('input[placeholder="Full Name"]').value;
  const email = signupForm.querySelector('input[placeholder="Email"]').value;
  //const password = signupForm.querySelector('input[placeholder="Password"]').value;
  const password = signupForm.querySelector('#password').value;


  const userData = {
    name,
    email,
    password,
    mobile: "1234567890" // Example static mobile value
  };

  try {
    // Send data to the server
    const response = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });

    if (response.ok) {
      const data = await response.json();
      alert('Registration successful!');
      console.log('Server response:', data);
    } else {
      const error = await response.json();
      alert('Registration failed: ' + (error.detail || 'Unknown error'));
    }
  } catch (err) {
    console.error('Network error:', err);
    alert('Network error. Please check your connection.');
  }
});

/**
 * Handle Login form submission (Optional)
 */
const loginForm = document.querySelector('.user_forms-login form');



loginForm.addEventListener('submit', async (e) => {
  e.preventDefault(); // Prevent default form submission

  const email = loginForm.querySelector('input[placeholder="Email"]').value;
  const password = loginForm.querySelector('input[placeholder="Password"]').value;

  const loginData = {
    email,
    password
  };

  try {
    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(loginData)
    });

    if (response.ok) {
      const data = await response.text();
      alert('Login successful!');
      console.log('Token received:', data);
    } else {
      const error = await response.json();
      alert('Login failed: ' + (error.detail || 'Unknown error'));
    }
  } catch (err) {
    console.error('Network error:', err);
    alert('Network error. Please check your connection.');
  }
});
