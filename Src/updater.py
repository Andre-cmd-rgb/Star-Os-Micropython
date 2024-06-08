import urequests
import uhashlib
import gc
gc.enable()
class Updater:
    raw = "https://raw.githubusercontent.com"
    github = "https://github.com"

    def __init__(self, user, repo, url=None, branch="master", working_dir="app", dest_dir=".", files=["boot.py", "main.py"], headers={}):
        """OTA updater class.

        Args:
            user (str): GitHub user.
            repo (str): GitHub repo to fetch.
            branch (str): GitHub repo branch. (master)
            working_dir (str): Directory inside GitHub repo where the micropython app is.
            dest_dir (str): Directory where files should be saved.
            url (str): URL to root directory.
            files (list): Files included in OTA update.
            headers (list, optional): Headers for urequests.
        """
        self.base_url = "{}/{}/{}".format(self.raw, user, repo) if user else url.replace(self.github, self.raw)
        self.url = url if url is not None else "{}/{}/{}".format(self.base_url, branch, working_dir)
        self.headers = headers
        self.files = files
        self.dest_dir = dest_dir

    def _check_hash(self, x, y):
        gc.collect()
        x_hash = uhashlib.sha1(x.encode())
        y_hash = uhashlib.sha1(y.encode())

        x = x_hash.digest()
        y = y_hash.digest()

        return x == y

    def _get_file(self, url):
        gc.collect()
        payload = urequests.get(url, headers=self.headers)
        code = payload.status_code

        if code == 200:
            return payload.text
        else:
            return None

    def _check_all(self):
        gc.collect()
        changes = []

        for file in self.files:
            latest_version = self._get_file(self.url + "/" + file)
            if latest_version is None:
                continue

            local_file_path = "{}/{}".format(self.dest_dir, file)

            try:
                with open(local_file_path, "r") as local_file:
                    local_version = local_file.read()
            except:
                local_version = ""

            if not self._check_hash(latest_version, local_version):
                changes.append(file)

        return changes

    def fetch(self):
        gc.collect()
        """Check if newer version is available.

        Returns:
            True - if is, False - if not.
        """
        return bool(self._check_all())

    def update(self):
        gc.collect()
        """Replace all changed files with newer one.

        Returns:
            True - if changes were made, False - if not.
        """
        changes = self._check_all()

        for file in changes:
            local_file_path = "{}/{}".format(self.dest_dir, file)
            with open(local_file_path, "w") as local_file:
                local_file.write(self._get_file(self.url + "/" + file))

        return bool(changes)