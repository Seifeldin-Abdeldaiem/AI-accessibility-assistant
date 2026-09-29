/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // STATIC_EXPORT=1 builds plain HTML/CSS/JS into out/ so the backend can
  // serve the site itself (one service, same origin). See the root
  // Dockerfile. Local development keeps the normal `next dev` server.
  ...(process.env.STATIC_EXPORT === "1" ? { output: "export" } : {}),
};

export default nextConfig;
