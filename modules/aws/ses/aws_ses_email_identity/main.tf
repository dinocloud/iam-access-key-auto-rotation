resource "aws_ses_email_identity" "ses_mails" {
  count     = var.mails_count
  email     = var.emails_list[count.index]
}