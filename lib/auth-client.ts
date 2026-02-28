import Cookies from 'js-cookie';

export function getClientPolicy() {
    const policy = Cookies.get('client_policy');
    if (policy) {
        try {
            return JSON.parse(policy);
        } catch (e) {
            return { role: 'Guest', permissions: [] };
        }
    }
    return { role: 'Guest', permissions: [] };
}