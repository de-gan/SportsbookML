import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import GoogleIcon from "@/assets/Google.svg"

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [policyAccepted, setPolicyAccepted] = useState(false);
  const [policyWarning, setPolicyWarning] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [termsWarning, setTermsWarning] = useState(false);
  const localUrl = import.meta.env.VITE_SITE_URL as string

  const redirectUrl = `${
    localUrl || window.location.origin
  }`;

  const registerWithGoogle = async () => {
    setError(null);
    if (!policyAccepted) {
      setPolicyWarning(true);
      setTermsWarning(true);
      return;
    }
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: redirectUrl },
    });
    if (error) {
      setError(error.message);
    }
  };
  
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!policyAccepted) {
      setPolicyWarning(true);
      setTermsWarning(true);
      return;
    }
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          display_name: displayName,
        },
      },
    });
    if (error) {
      setError(error.message);
    } else {
      setMessage("Check your email for a confirmation link.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <form className="space-y-4" onSubmit={handleSignUp}>
            <Input
              type="text"
              placeholder="Display Name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && <div className="text-sm text-red-500">{error}</div>}
            {message && <div className="text-sm text-green-600">{message}</div>}
            <details className="border rounded p-2">
              <summary className="cursor-pointer select-none">
                Privacy Policy
              </summary>
              <div className="mt-2 text-sm space-y-2">
                <p>
                  We value your privacy. Your information will only be used to
                  provide our services and will not be shared with third
                  parties.
                  <br/><br/>

                  <em>Last updated: Aug. 26, 2025</em>
                  <br/><br/>

                  UpperHand (“we,” “our,” or “us”) respects your privacy. This Privacy Policy explains how we collect, use, and protect your personal information when you register for and use our betting assistance service.
                  <br/><br/>

                  <b>Information We Collect</b>
                  <br/>
                  Email Address: Collected during registration to create your account.
                  <br/>
                  No Other Data: We do not collect, store, or process any other personal information you provide beyond your email.
                  <br/><br/>

                  <b>How We Use Your Information</b>
                  <br/>
                  Service Communication: Your email is used only to manage your account and provide necessary updates about the service or your subscription.
                  <br/>
                  Optional Updates: From time to time, we may send you updates about new features or service announcements. You may opt out of these communications at any time by following the unsubscribe instructions provided in the email.
                  <br/><br/>

                  <b>Data Sharing</b>
                  <br/>

                  We do not sell, rent, trade, or share your information with third parties.
                  <br/>
                  Your data is used solely to operate and improve this service.
                  <br/><br/>

                  <b>Data Security</b>
                  <br/>
                  We take appropriate security measures to protect your email and ensure it is not lost, misused, or accessed without authorization.
                  <br/><br/>

                  <b>Your Rights</b>
                  <br/>
                  You may request to update or delete your email and account at any time.
                  <br/>
                  You may unsubscribe from non-essential communications using the "Opt-out of these emails" link provided in our emails (sent via Supabase).
                  <br/><br/>

                  <b>Children’s Privacy</b>
                  <br/>
                  This service is not directed toward individuals under the age of 18. We do not knowingly collect information from children.
                  <br/><br/>

                  <b>Changes to This Policy</b>
                  <br/>
                  We may update this Privacy Policy occasionally. If we make material changes, we will notify you via email or through the service.
                  <br/><br/>

                  <b>Contact Us</b>
                  <br/>
                  If you have any questions about this Privacy Policy or how your data is handled, please contact us at:
                  denmgannon@gmail.com
                </p>
              </div>
            </details>
            <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={policyAccepted}
                  onChange={(e) => {
                    setPolicyAccepted(e.target.checked);
                    if (e.target.checked) {
                      setPolicyWarning(false);
                    }
                  }}
                />
                <span>I agree to the privacy policy</span>
              </label>
            {policyWarning && (
              <div className="text-xs text-red-500">
                You must accept the privacy policy
              </div>
            )}
            <details className="border rounded p-2">
              <summary className="cursor-pointer select-none">
                Terms & Conditions
              </summary>
              <div className="mt-2 text-sm space-y-2">
                <p>
                  <em>Last updated: Aug. 26, 2025</em>
                  <br/><br/>
                  Welcome to UpperHand (“we,” “our,” or “us”). By registering for and using our betting assistance service (the “Service”), you agree to the following Terms & Conditions. Please read them carefully. If you do not agree, you may not use the Service.
                  <br/><br/>
                  <b>1. Use of the Service</b>
                  <br/>
                  • The Service is provided for informational and educational purposes only.
                  <br/>
                  • We are not a financial advisor and nothing in the Service constitutes financial or investment advice.
                  <br/>
                  • We do not guarantee any winnings, outcomes, or success in sports betting or other activities.
                  <br/><br/>

                  <b>2. User Responsibilities</b>
                  <br/>
                  When using the Service, you agree that you will not:
                  <br/>
                  • Use the Service for any illegal betting or gambling activities.
                  <br/>
                  • Scrape, copy, or extract data from the Service without our written permission.
                  <br/>
                  • Engage in activity that disrupts or harms the Service or other users.
                  <br/>
                  Violations of these rules may result in suspension or termination of your account without notice.
                  <br/><br/>

                  <b>3. Account & Privacy</b>
                  <br/>
                  • You must provide a valid email address to register.
                  <br/>
                  • You are responsible for keeping your account secure.
                  <br/>
                  • By using the Service, you agree to our <em>Privacy Policy</em>, which explains how we handle your data.
                  <br/><br/>

                  <b>4. Disclaimer of Warranties</b>
                  <br/>
                  The Service is provided “as is” and “as available.”
                  <br/>
                  • We make no warranties or guarantees about the accuracy, reliability, or availability of the Service.
                  <br/>
                  • Your use of the Service is at your own risk.
                  <br/><br/>

                  <b>5. Limitation of Liability</b>
                  <br/>
                  To the maximum extent permitted by law:
                  <br/>
                  • We are not liable for any losses, damages, or consequences resulting from use of the Service, including financial losses from betting.
                  <br/>
                  • You agree that we are not responsible for actions you take based on information provided.
                  <br/><br/>

                  <b>6. Dispute Resolution</b>
                  <br/>
                  If a dispute arises between you and us:
                  <br/>
                  • We encourage you to contact us first to seek an informal resolution.
                  <br/>
                  • If unresolved, disputes will be handled through binding arbitration in [Insert State/Country].
                  <br/>
                  • You waive your right to participate in a class action lawsuit.
                  <br/><br/>

                  <b>7. Changes to These Terms</b>
                  <br/>
                  We may update these Terms occasionally. If material changes are made, we will notify you via email or through the Service. Continued use after changes means you accept the revised Terms.
                  <br/><br/>

                  <b>8. Contact Us</b>
                  <br/>
                  If you have questions about these Terms & Conditions, please contact us at:
                  denmgannon@gmail.com
                </p>
              </div>
            </details>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={termsAccepted}
                onChange={(e) => {
                  setTermsAccepted(e.target.checked);
                  if (e.target.checked) {
                    setTermsWarning(false);
                  }
                }}
              />
              <span>I agree to the terms & conditions</span>
            </label>
            {termsWarning && (
              <div className="text-xs text-red-500">
                You must accept the terms & conditions
              </div>
            )}
            <Button type="submit" className="w-full">
              Register
            </Button>
            <Button
              type="button"
              className="w-full"
              onClick={registerWithGoogle}
            >
              <img
                src={GoogleIcon}
                alt="Google logo"
                className="h-4 w-4"
              />
              Sign up with Google
            </Button>
            <Button asChild variant="secondary" className="w-full">
              <Link to="/login">Already have an account?</Link>
            </Button>
            <Button asChild variant="ghost" className="w-full">
              <Link to="/">Back to Home</Link>
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
