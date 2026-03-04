import axios from 'axios'

// Attach token from localStorage to every request
axios.interceptors.request.use((config) => {
    try {
        const token = localStorage.getItem('token')
        if (token) config.headers = { ...config.headers, Authorization: `Bearer ${token}` }
    } catch (e) {
        // ignore (no localStorage available)
    }
    return config
}, (error) => Promise.reject(error))

// Global response handler: on 401, clear auth and redirect to login
axios.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err && err.response && err.response.status === 401) {
            try {
                localStorage.removeItem('token')
            } catch (e) { }
            // notify app + redirect to login for re-auth
            window.dispatchEvent(new CustomEvent('auth-unauthorized'))
            // Small delay to allow any listeners to run
            setTimeout(() => { window.location.href = '/login' }, 100)
        }
        return Promise.reject(err)
    }
)

export default axios
