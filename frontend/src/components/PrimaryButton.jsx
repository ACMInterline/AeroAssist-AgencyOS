import { forwardRef } from "react"
import ActionButton from "./ActionButton"

const PrimaryButton = forwardRef(function PrimaryButton(props, ref) {
  return <ActionButton ref={ref} variant="primary" {...props} />
})

export default PrimaryButton
