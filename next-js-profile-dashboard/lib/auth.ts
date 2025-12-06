export function getLoggedInPhone(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('userPhone');
}

export function setLoggedInPhone(phone: string): void {
  localStorage.setItem('userPhone', phone);
}

export function logout(): void {
  localStorage.removeItem('userPhone');
}

export function isLoggedIn(): boolean {
  return !!getLoggedInPhone();
}
