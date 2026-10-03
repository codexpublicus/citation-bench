//! Stamps the citare version and commit that the build task resolved into the adapter,
//! which reports them in its reply to the bench's probe (docs/protocol.md).
fn main() {
    for var in ["CITARE_VERSION", "CITARE_COMMIT"] {
        println!("cargo:rerun-if-env-changed={var}");
        let value = std::env::var(var).unwrap_or_else(|_| "unknown".into());
        println!("cargo:rustc-env={var}={value}");
    }
}
