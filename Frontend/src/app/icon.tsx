import { ImageResponse } from 'next/og';


export const runtime = 'edge';


export const size = {
  width: 32,
  height: 32,
};
export const contentType = 'image/png';


export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 24,
          background: '#0EA5A4',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          borderRadius: '4px',
        }}
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M8 7h8M8 12h8M8 17h5"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <circle cx="18" cy="17" r="1.5" fill="white" />
        </svg>
      </div>
    ),
    {
      ...size,
    }
  );
}
