interface SpinnerProps { size?: number; }
export default function Spinner({ size = 20 }: SpinnerProps) {
  return <span className="spinner" style={{ width: size, height: size }} />;
}
