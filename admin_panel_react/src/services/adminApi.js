
import {
  registerAdmin as _registerAdmin,
  loginAdmin as _loginAdmin,
  adminMe as _adminMe,
} from "@/services/authApi";

export function registerAdmin(payload) {
  return _registerAdmin(payload);
}
export function loginAdmin({ email, password }) {
  return _loginAdmin({ email, password });
}
export function adminMe() {
  return _adminMe();
}