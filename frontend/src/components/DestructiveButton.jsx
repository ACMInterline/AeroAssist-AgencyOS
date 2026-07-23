import { forwardRef } from "react"
import ActionButton from "./ActionButton"

const DestructiveButton = forwardRef(function DestructiveButton(props, ref) {
  return <ActionButton ref={ref} variant="destructive" {...props} />
})

export default DestructiveButton
