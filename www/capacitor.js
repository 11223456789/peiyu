// Capacitor Bridge - 用于Web和原生APP之间的通信
// 如果在原生APP中运行，使用Capacitor插件
// 如果在浏览器中运行，降级到localStorage和fetch

const Capacitor = {
    Plugins: {
        Preferences: {
            get: async ({ key }) => {
                const value = localStorage.getItem(key);
                return { value };
            },
            set: async ({ key, value }) => {
                localStorage.setItem(key, value);
            },
            remove: async ({ key }) => {
                localStorage.removeItem(key);
            }
        },
        Http: {
            request: async (options) => {
                // 使用fetch模拟HTTP请求
                try {
                    const response = await fetch(options.url, {
                        method: options.method || 'GET',
                        headers: options.headers || {},
                        body: options.data
                    });
                    
                    const data = await response.text();
                    return {
                        data: data,
                        status: response.status,
                        headers: {}
                    };
                } catch (e) {
                    throw new Error('Network error: ' + e.message);
                }
            }
        },
        Toast: {
            show: async ({ text }) => {
                // 使用自定义toast
                const toast = document.getElementById('toast');
                if (toast) {
                    toast.textContent = text;
                    toast.classList.add('show');
                    setTimeout(() => toast.classList.remove('show'), 2000);
                }
            }
        },
        App: {
            exitApp: async () => {
                // Web环境无法退出
                console.log('Exit app requested');
            }
        }
    },
    
    isNativePlatform: () => {
        // 检查是否在原生平台
        return typeof window !== 'undefined' && 
               window.Capacitor && 
               window.Capacitor.isNative;
    }
};

// 如果在原生环境中，使用真正的Capacitor
if (typeof window !== 'undefined' && window.Capacitor) {
    Object.assign(Capacitor, window.Capacitor);
}
