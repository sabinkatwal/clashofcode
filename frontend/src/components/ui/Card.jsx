import './Card.css';

export default function Card({ children, className = '', glow = false, ...props }) {
  return (
    <div className={`card ${glow ? 'card-glow' : ''} ${className}`} {...props}>
      {children}
    </div>
  );
}
