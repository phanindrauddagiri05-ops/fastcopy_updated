from waitress import serve
from fastCopyConfig.wsgi import application
import os

if __name__ == '__main__':
    # Determine port from environment or default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting FastCopy Production Server on http://localhost:{port}")
    print(f"   - Workers: 6 (Optimized for 6-core CPU)")
    print(f"   - Static Compression: Enabled (WhiteNoise)")
    print(f"   - Database Pooling: Enabled (60s persistence)")
    
    # Run Waitress with optimized persistent connections
    serve(application, host='0.0.0.0', port=port, threads=6)
