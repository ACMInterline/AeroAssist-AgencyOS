import StatusBadge from "./StatusBadge"

export default function AirlineStatusBadge({ status }) {
  return <StatusBadge status={status || "active"} />
}
