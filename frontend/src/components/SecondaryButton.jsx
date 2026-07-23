import { forwardRef } from "react"
import ActionButton from "./ActionButton"

const SecondaryButton = forwardRef(function SecondaryButton(props, ref) {
  return <ActionButton ref={ref} variant="secondary" {...props} />
})

export default SecondaryButton
