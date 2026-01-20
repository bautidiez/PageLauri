import { isDevMode } from '@angular/core';

export const environment = {
  production: !isDevMode(),
  apiUrl: !isDevMode()
    ? 'https://elvestuario-backend.onrender.com/api'
    : 'http://localhost:5000/api'
};
