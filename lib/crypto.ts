import CryptoJS from 'crypto-js';

const SECRET_KEY = process.env.JWT_SECRET || 'your-fallback-secret-key-must-be-long';

export const encryptData = (data: any) => {
  return CryptoJS.AES.encrypt(JSON.stringify(data), SECRET_KEY).toString();
};

export const decryptData = (ciphertext: string) => {
  try {
    const bytes = CryptoJS.AES.decrypt(ciphertext, SECRET_KEY);
    return JSON.parse(bytes.toString(CryptoJS.enc.Utf8));
  } catch (e) {
    console.error('Decryption failed', e);
    return null;
  }
};