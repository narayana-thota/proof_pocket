
export default function Logo({ compact = false }) {
  return (
    <div className="brand">
      <svg
        className="brand-symbol"
        viewBox="0 0 180 150"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label="ProofPocket"
      >
        <defs>
          <linearGradient id="pp-purple" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#8756FF" />
            <stop offset="100%" stopColor="#4822B8" />
          </linearGradient>
        </defs>

        {/* Documents */}
        <path
          d="M43 18 Q43 11 52 11 H111 L133 32 V76 H43 Z"
          fill="#7043E5"
        />
        <path d="M111 11 V32 H133 Z" fill="#C8B7FF" />
        <path
          d="M57 26 H112 M54 39 H109"
          stroke="#FFFFFF"
          strokeWidth="6"
          strokeLinecap="round"
        />

        {/* Pocket */}
        <path
          d="M29 58 Q29 49 39 49 H139 Q150 49 150 60 V103 Q150 116 137 116 H42 Q29 116 29 103 Z"
          fill="url(#pp-purple)"
        />

        {/* Pocket rim */}
        <path
          d="M29 60 L41 48 H137 L150 60"
          stroke="#4822B8"
          strokeWidth="4"
          fill="none"
        />

        {/* P */}
        <text
          x="90"
          y="103"
          textAnchor="middle"
          fontSize="59"
          fontWeight="800"
          fontStyle="italic"
          fontFamily="Arial, sans-serif"
          fill="white"
        >
          P
        </text>
      </svg>

      {!compact && (
        <span className="brand-name">
          Proof<span>Pocket</span>
        </span>
      )}
    </div>
  );
}
